"""Train-condition-only material fits; whole-episode validation and tests.

Two distinct outputs: measured-motion constitutive diagnostics, and optional
command-conditioned forecasts requiring an independently calibrated actuator.
No model family is selected using test scores.
"""
import argparse,hashlib,time,platform
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from mechanisms import MODELS,rollout,unpack,initial_parameters,parameters_json
from pilot_io import ROOT,load_dataset,splits,local_output,write_csv,write_json,contact_position

def predict(ep,p,name,meta,command=False,step=None):
    step=meta.get('analysis',{}).get('max_step_s',.01) if step is None else step
    if meta.get('data_type')=='real' and (step is None or step<=0):
        raise ValueError('Set max_step_s from pretest timescales before fitting real data')
    if meta.get('analysis',{}).get('constitutive_only') and command:
        raise ValueError('This first-batch path is constitutive only; planned commands and actuator validation are separate')
    plant=meta.get('actuator',{})
    if command and not (plant.get('calibrated') and plant.get('provenance')):
        raise ValueError('Command forecast requires documented independent actuator calibration')
    if command and any(k not in plant or not np.isfinite(plant[k]) or plant[k]<=0 for k in ['mass_kg','stiffness_N_m','damping_N_s_m']):
        raise ValueError('Actuator calibration must provide positive mass_kg, stiffness_N_m, damping_N_s_m; no synthetic defaults')
    actuator=np.array([plant['mass_kg'],plant['stiffness_N_m'],plant['damping_N_s_m']]) if command else np.ones(3)
    observed=ep['x'].copy()
    if command:observed[ep['forecast']:]=np.nan  # Guard against future measured-motion leakage.
    return rollout(ep['t'],ep['u'],observed,*unpack(p,name),meta['analysis']['reference_compression_m'],actuator,
                   ep['forecast'] if command else -1,step,name.startswith('Q'))

def weights(ep):
    # Equal weight per episode and per informative phase; all samples retained.
    w=np.zeros(len(ep['t']));dt=np.r_[np.diff(ep['t']),np.diff(ep['t'])[-1]]
    for phase in ['preload','hold','retract','recontact','rehold']:
        mask=ep['phase']==phase
        w[mask]=np.sqrt(dt[mask]/dt[mask].sum()/5)
    return w

def residual(p,name,episodes,meta):
    return np.concatenate([(predict(e,p,name,meta)[0]-e['f'])*weights(e)/np.sqrt(len(episodes)) for e in episodes])

def fit_model(name,train,val,meta,starts=2,max_nfev=250,initial_override=None):
    ref=meta['analysis']['reference_compression_m'];scale=max(np.max(e['f']) for e in train)
    p,low,high=initial_parameters(name,ref,scale,max(e['t'][-1] for e in train))
    # Real-record bandwidth/duration determine the identifiable spectral window.
    # Do not inherit a 20 ms minimum time constant from synthetic examples.
    config=meta.get('analysis',{})
    if config.get('tau_min_s') is not None and config.get('tau_max_s') is not None:
        n=MODELS[name][0];lo=float(config['tau_min_s']);hi=float(config['tau_max_s'])
        if not 0<lo<hi:raise ValueError('Require 0 < tau_min_s < tau_max_s')
        low[1+n:1+2*n]=np.log(lo);high[1+n:1+2*n]=np.log(hi)
        p[1+n:1+2*n]=np.log(np.geomspace(lo*1.01,hi/1.01,n))
    rng=np.random.default_rng(20261019);records=[];solutions=[];start=time.perf_counter()
    for j in range(starts):
        initial=(p.copy() if initial_override is None else np.clip(initial_override,low+1e-5,high-1e-5)) if j==0 else np.clip(p+rng.normal(0,.35,len(p)),low+1e-4,high-1e-4)
        tic=time.perf_counter()
        r=least_squares(residual,initial,bounds=(low,high),args=(name,train,meta),max_nfev=max_nfev,
            ftol=1e-7,xtol=1e-7,gtol=1e-7,x_scale='jac')
        validation=float(np.sum(residual(r.x,name,val,meta)**2))
        sv=np.linalg.svd(r.jac,compute_uv=False)
        records.append(dict(start=j,initial_parameters=initial.tolist(),final_parameters=r.x.tolist(),success=bool(r.success),status=int(r.status),message=r.message,nfev=r.nfev,
            train_phase_balanced_mse_N2=float(2*r.cost),validation_phase_balanced_mse_N2=validation,
            optimality=float(r.optimality),seconds=time.perf_counter()-tic,
            jacobian_singular_values=sv.tolist(),bound_proximity=bool(np.any(np.minimum(r.x-low,high-r.x)<.005))))
        solutions.append(r.x)
    valid=[i for i,r in enumerate(records) if r['success']]
    if not valid:raise RuntimeError(f'{name}: no converged start; raise budget explicitly, do not report comparison')
    winner=min(valid,key=lambda i:records[i]['validation_phase_balanced_mse_N2'])
    return solutions[winner],dict(selected_start=winner,starts=records,seconds=time.perf_counter()-start,
               selection='validation episodes only, among optimizer-converged starts',params=parameters_json(solutions[winner],name))

def evaluate_one(ep,force,x,meta):
    target=(ep['phase']=='recontact')|(ep['phase']=='rehold')
    t=ep['t'];dt=np.r_[np.diff(t),np.diff(t)[-1]];w=dt[target]/sum(dt[target]);err=force[target]-ep['f'][target]
    threshold=meta['analysis']['contact_threshold_N'];persist=meta['analysis']['contact_persistence_s']
    actual_cp=contact_position(t,ep['x'],ep['f'],ep['phase'],threshold,persist)
    pred_cp=contact_position(t,x,force,ep['phase'],threshold,persist)
    return dict(force_rmse_N=float(np.sqrt(np.sum(w*err**2))),force_bias_N=float(np.sum(w*err)),
       position_rmse_mm=float(1000*np.sqrt(np.sum(w*(x[target]-ep['x'][target])**2))),
       peak_error_N=float(np.max(force[target])-np.max(ep['f'][target])),
       impulse_error_Ns=float(np.trapezoid(force[target]-ep['f'][target],t[target])),
       contact_position_error_mm=None if actual_cp is None or pred_cp is None else float(1000*(pred_cp-actual_cp)),
       contact_actual_detected=actual_cp is not None,contact_prediction_detected=pred_cp is not None)

def run(dataset,out,models,axes,starts=2,max_nfev=250):
    out=local_output(out);episodes,meta,checks=load_dataset(dataset);start=time.perf_counter()
    write_json(out/'data_checks.json',checks);write_json(out/'metadata.json',meta)
    write_json(out/'provenance.json',dict(dataset=str(Path(dataset).resolve()),data_type=meta['data_type'],
       hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(dataset).glob('*') if p.suffix in ['.csv','.json']},
       models=models,axes=axes,starts=starts,max_nfev=max_nfev,python=platform.python_version()))
    # Incremental model additions preserve earlier per-model fits and predictions.
    existing=out/'metrics.csv'
    if existing.exists():
        import csv
        with existing.open(encoding='utf-8-sig',newline='') as f:metrics=[r for r in csv.DictReader(f) if r['model'] not in models or r['axis'] not in axes]
        for r in metrics:
            for field in ['force_rmse_N','force_bias_N','position_rmse_mm','peak_error_N','impulse_error_Ns','contact_position_error_mm']:
                r[field]=float(r[field]) if r[field] not in ['',None] else None
        predictions={k:v for k,v in np.load(out/'predictions.npz').items() if not(k.split('__')[0] in axes and k.split('__')[1] in models)}
        from pilot_io import read_json
        fits=read_json(out/'fits.json');split_manifest=read_json(out/'splits.json')
    else:metrics=[];predictions={};fits={};split_manifest={}
    for axis,pool,test in splits(episodes):
        if axis not in axes:continue
        repeat=min(int(e['repeat']) for e in pool)
        train=[e for e in pool if int(e['repeat'])==repeat];val=[e for e in pool if int(e['repeat'])!=repeat]
        if not val:raise ValueError('Need independent validation repeat in every training condition')
        split_manifest[axis]={'fit':[e['key'] for e in train],'validation':[e['key'] for e in val],'test':[e['key'] for e in test]}
        for name in models:
            parent={'L4':'L2','S2':'L2','R2':'L2','SR2':'R2','S4':'S2','Q2':'L2','Q4':'Q2',
                    'L6':'L4','S6':'S4','Q6':'Q4'}.get(name)
            warm=None
            if parent and f'{axis}/{parent}' in fits:
                base=np.array(fits[f'{axis}/{parent}']['p']);m,static,rate=MODELS[name]
                if MODELS[name][0]>MODELS[parent][0]:
                    old=MODELS[parent][0]
                    # Split existing branch stiffnesses without changing the nested law.
                    ids=np.arange(m)%old;counts=np.bincount(ids,minlength=old)
                    warm=np.r_[base[0],base[1:1+old][ids]-np.log(counts[ids]),
                               base[1+old:1+2*old][ids],base[1+2*old:]]
                elif name=='SR2':warm=np.r_[base[:5],0.,base[5]]
                else:warm=np.r_[base,0.]
            p,fit=fit_model(name,train,val,meta,starts,max_nfev,warm);fit['p']=p.tolist();fit['warm_start_parent']=parent;fits[f'{axis}/{name}']=fit
            print(f'{axis}/{name} {fit["seconds"]:.1f}s val={fit["starts"][fit["selected_start"]]["validation_phase_balanced_mse_N2"]:.6g}',flush=True)
            for ep in test:
                modes=['constitutive']+(['command'] if meta.get('actuator',{}).get('calibrated')
                    and not meta.get('analysis',{}).get('constitutive_only') else [])
                for mode in modes:
                    force,x,z,e=predict(ep,p,name,meta,mode=='command')
                    key=f'{axis}__{name}__{ep["episode_id"]}__{mode}'
                    predictions[key]=np.stack([force,x,e],axis=-1)
                    metrics.append(dict(axis=axis,model=name,mode=mode,episode_id=ep['episode_id'],
                        repeat=ep['repeat'],amplitude_m=ep['amplitude'],wait_s=ep['wait'],program=ep['program'],
                        **evaluate_one(ep,force,x,meta)))
            write_json(out/'fits.json',fits)
    np.savez_compressed(out/'predictions.npz',**predictions);write_csv(out/'metrics.csv',metrics)
    write_json(out/'splits.json',split_manifest)
    summary=[]
    for axis in sorted({r['axis'] for r in metrics}):
        for name in MODELS:
            for mode in ['constitutive','command']:
                rows=[r for r in metrics if r['axis']==axis and r['model']==name and r['mode']==mode]
                if not rows:continue
                summary.append(dict(axis=axis,model=name,mode=mode,n_episodes=len(rows),
                    median_force_rmse_N=float(np.median([r['force_rmse_N'] for r in rows])),
                    mean_force_rmse_N=float(np.mean([r['force_rmse_N'] for r in rows]))))
    write_csv(out/'summary.csv',summary);write_json(out/'cost.json',dict(latest_invocation_seconds=time.perf_counter()-start,
         cumulative_fit_seconds=sum(f['seconds'] for f in fits.values()),GPU_used=False,compiled_cpu=True,fit_count=len(fits),
         notes='No neural training. JIT warm-up included if cold. Cumulative sums per-model fit durations; excludes plotting.'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('dataset');p.add_argument('--output',required=True)
    p.add_argument('--models',nargs='+',choices=list(MODELS),default=list(MODELS));p.add_argument('--axes',nargs='+',default=['amplitude','wait','program'])
    p.add_argument('--starts',type=int,default=2);p.add_argument('--max-nfev',type=int,default=250);a=p.parse_args()
    run(a.dataset,a.output,a.models,a.axes,a.starts,a.max_nfev)

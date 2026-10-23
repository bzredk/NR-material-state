"""Reproducible pilot: prepare/profile -> train -> evaluate/report figures.
All outputs stay below this project. Test results never select checkpoints.
"""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'.cache'/'matplotlib'))
os.environ.setdefault('CUDA_CACHE_PATH', str(ROOT/'.cache'/'cuda'))
import argparse
import copy
import csv
import hashlib
import json
import platform
import random
import sys
import time
from datetime import datetime, timezone
import numpy as np
import scipy
from scipy.optimize import least_squares
import torch
from data import generate, load, command_protocol
from physics import Material, simulate, ground_history, observe_force_from_positions
from models import MODELS, prediction_loss


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def set_seed(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.set_num_threads(4)


def synchronize(device):
    if device == 'cuda': torch.cuda.synchronize()


def tensors(ds, device):
    # Deliberate whitelist: no simulator states, clean future labels, or contact flags.
    return tuple(torch.tensor(ds[key], device=device) for key in ['history', 'commands', 'labels'])


def numerical_checks(cfg):
    u, _, _ = command_protocol(cfg, 777, 1.)
    mat = Material.from_dict(cfg['truth'])
    times = np.arange(len(u))*cfg['dt']
    results=[]
    for factor in [1,2,4]:
        ts = np.arange((len(u)-1)*factor+1)*cfg['dt']/factor
        cmd = np.interp(ts,times,u)[None]
        y=simulate(cmd,mat,cfg['plant'],cfg['dt']/factor)[0][0,::factor]
        results.append(y)
    force_errors=[float(np.sqrt(np.mean((results[i][:,2]-results[2][:,2])**2))) for i in [0,1]]
    pos_errors=[float(np.sqrt(np.mean((results[i][:,0]-results[2][:,0])**2))*1000) for i in [0,1]]
    return {'reference_dt':cfg['dt']/4,'force_rmse_N_vs_reference':force_errors,
            'position_rmse_mm_vs_reference':pos_errors,
            'refinement_improves': force_errors[1]<force_errors[0] and pos_errors[1]<pos_errors[0],
            'interpretation':'Generated data and predictors share dt; reference discrepancy is a numerical fidelity limit.'}


def prepare(cfg, out, device):
    t0=time.perf_counter()
    ds=generate(cfg,out/'data')
    generation_seconds=time.perf_counter()-t0
    env={'utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'executable':sys.executable,
         'platform':platform.platform(),'torch':torch.__version__,'numpy':np.__version__,
         'scipy':scipy.__version__,'cuda_runtime':torch.version.cuda,'device':device,
         'gpu':torch.cuda.get_device_name(0) if device=='cuda' else None,
         'gpu_total_memory_GiB':torch.cuda.get_device_properties(0).total_memory/2**30 if device=='cuda' else None,
         'git_note':'This project was created in a non-git workspace; SHA256 manifest records sources.'}
    write_json(out/'environment.json',env)
    write_json(out/'numerical_checks.json',numerical_checks(cfg))
    profile={'data_generation_seconds':generation_seconds,'models':{}}
    for name, cls in MODELS.items():
        set_seed(0)
        model=cls(cfg).to(device)
        opt=torch.optim.Adam(model.parameters(),lr=cfg['learning_rate'])
        batch={k:v[:cfg['batch_size']] for k,v in ds['train'].items()}
        h,u,y=tensors(batch,device)
        if device=='cuda': torch.cuda.reset_peak_memory_stats()
        times=[]
        for it in range(6):
            synchronize(device); t=time.perf_counter()
            opt.zero_grad(set_to_none=True)
            pred=model(h,u); loss=prediction_loss(pred,y)
            loss.backward(); opt.step()
            synchronize(device)
            if it>=2: times.append(time.perf_counter()-t)
        profile['models'][name]={'train_step_seconds_median':float(np.median(times)),
            'train_step_seconds_samples':times,'parameters':sum(p.numel() for p in model.parameters()),
            'peak_allocated_MiB':torch.cuda.max_memory_allocated()/2**20 if device=='cuda' else None,
            'peak_reserved_MiB':torch.cuda.max_memory_reserved()/2**20 if device=='cuda' else None,
            'batch':cfg['batch_size'],'history_steps':cfg['history_steps']+1,'future_steps':cfg['future_steps']}
        print('PROFILE',name,json.dumps(profile['models'][name]),flush=True)
        del model,opt,h,u,y,pred,loss
        if device=='cuda': torch.cuda.empty_cache()
    slow=max(v['train_step_seconds_median'] for v in profile['models'].values())
    proposed=int(cfg['profile_target_seconds_per_run']/slow)
    interval=cfg['validation_interval']
    steps=cfg.get('fixed_steps') or max(cfg['min_steps'],min(cfg['max_steps'],proposed//interval*interval))
    plan={'training_steps_per_run':steps,'seeds':cfg['seeds'],
          'selection':'Same number of optimizer updates, chosen from pre-training profiling; no test access.',
          'estimated_training_seconds_without_validation':sum(v['train_step_seconds_median']*steps*len(cfg['seeds']) for v in profile['models'].values()),
          'hyperparameter_trials_per_model':1,'configuration':cfg}
    write_json(out/'profile.json',profile);write_json(out/'training_plan.json',plan)
    write_json(out/'config.json',cfg)
    print('PLAN',json.dumps({k:v for k,v in plan.items() if k!='configuration'}),flush=True)


def fit_classical(cfg, ds, out):
    # Standard system identification: measured motion -> measured force in TRAIN ONLY.
    xs=ds['train']['full_observed'][...,0]
    fs=ds['train']['full_observed'][...,2]
    fitted={}
    for modes in [0,1,2]:
        started=time.perf_counter()
        if modes==0:
            xp=np.maximum(xs,0)
            mat=Material(max(1.,float(np.sum(xp*fs)/np.sum(xp*xp))),np.zeros(0),np.zeros(0))
            info={'nfev':1,'success':True}
        else:
            initial=([600.,1700.,.7] if modes==1 else [600.,700.,1000.,.25,2.])
            def unpack(logp):
                p=np.exp(logp)
                return Material(p[0],p[1:1+modes],p[1+modes:])
            def residual(logp):
                pred=observe_force_from_positions(xs,unpack(logp),cfg['dt'])
                return ((pred-fs)/8.).ravel()
            lo=np.log([20.]*(modes+1)+[.02]*modes)
            hi=np.log([10000.]*(modes+1)+[10.]*modes)
            fit=least_squares(residual,np.log(initial),bounds=(lo,hi),max_nfev=100,
                              ftol=1e-9,xtol=1e-9,gtol=1e-9)
            mat=unpack(fit.x)
            order=np.argsort(mat.tau);mat.k=mat.k[order];mat.tau=mat.tau[order]
            info={'nfev':fit.nfev,'success':bool(fit.success),'cost':float(fit.cost)}
        info.update(parameters=mat.as_dict(),seconds=time.perf_counter()-started,
                    training_episodes=len(xs),supervision='train measured position and force only')
        fitted[f'classical_{modes}']=info
        print('CLASSICAL',modes,json.dumps(info),flush=True)
    write_json(out/'classical_fits.json',fitted)


def train(cfg,out,device):
    ds=load(out/'data')
    fit_classical(cfg,ds,out)
    plan=json.loads((out/'training_plan.json').read_text())
    train_h,train_u,train_y=tensors(ds['train'],device)
    val_h,val_u,val_y=tensors(ds['val'],device)
    (out/'checkpoints').mkdir(exist_ok=True)
    (out/'logs').mkdir(exist_ok=True)
    for name,cls in MODELS.items():
        for seed in cfg['seeds']:
            set_seed(seed)
            model=cls(cfg).to(device)
            opt=torch.optim.Adam(model.parameters(),lr=cfg['learning_rate'])
            indices=np.random.default_rng(seed+100)
            best=float('inf');best_step=-1;log=[]
            if device=='cuda': torch.cuda.reset_peak_memory_stats()
            synchronize(device);started=time.perf_counter()
            for it in range(plan['training_steps_per_run']+1):
                if it>0:
                    model.train()
                    idx=torch.tensor(indices.choice(len(train_h),cfg['batch_size'],replace=False),device=device)
                    opt.zero_grad(set_to_none=True)
                    pred=model(train_h[idx],train_u[idx]);loss=prediction_loss(pred,train_y[idx])
                    if not torch.isfinite(loss): raise RuntimeError(f'nonfinite {name} {seed} {it}')
                    loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.)
                    opt.step()
                if it % cfg['validation_interval']==0 or it==plan['training_steps_per_run']:
                    model.eval()
                    with torch.no_grad():
                        vl=float(prediction_loss(model(val_h,val_u),val_y))
                    synchronize(device)
                    record={'step':it,'train_loss':float(loss.detach()) if it>0 else None,
                            'val_loss':vl,'elapsed_seconds':time.perf_counter()-started}
                    log.append(record)
                    if vl<best:
                        best=vl;best_step=it
                        torch.save({'state_dict':model.state_dict(),'model':name,'seed':seed,'step':it,
                                    'validation_loss':vl,'config':cfg},out/'checkpoints'/f'{name}_{seed}.pt')
                    print('TRAIN',name,seed,json.dumps(record),flush=True)
                    write_json(out/'logs'/f'{name}_{seed}.json',log)
            synchronize(device)
            metadata={'model':name,'seed':seed,'best_step':best_step,'best_val_loss':best,
                      'seconds':time.perf_counter()-started,'optimizer_steps':plan['training_steps_per_run'],
                      'peak_allocated_MiB':torch.cuda.max_memory_allocated()/2**20 if device=='cuda' else None,
                      'parameters':sum(p.numel() for p in model.parameters()),'finished':True}
            write_json(out/'logs'/f'{name}_{seed}_meta.json',metadata)
            print('COMPLETE',json.dumps(metadata),flush=True)


def episode_metrics(pred,ds):
    target=ds['truth'];mask=ds['metric_mask']
    counts=mask.sum(1)
    f=np.sqrt((((pred[...,2]-target[...,2])**2)*mask).sum(1)/counts)
    x=np.sqrt((((pred[...,0]-target[...,0])**2)*mask).sum(1)/counts)*1000
    peak=np.abs(np.where(mask,pred[...,2],-np.inf).max(1)-np.where(mask,target[...,2],-np.inf).max(1))
    return dict(force_rmse_N=f,position_rmse_mm=x,peak_force_error_N=peak,
                whole_force_rmse_N=np.sqrt(((pred[...,2]-target[...,2])**2).mean(1)))


def bootstrap(a,seed=991):
    # a = optimization seeds x independent test episode groups.
    rng=np.random.default_rng(seed);a=np.asarray(a);S,N=a.shape
    means=[]
    for _ in range(1500):
        si=rng.integers(0,S,S);ni=rng.integers(0,N,N)
        means.append(a[si][:,ni].mean())
    return dict(mean=float(a.mean()),ci_low=float(np.quantile(means,.025)),
                ci_high=float(np.quantile(means,.975)),
                seed_means=a.mean(1).tolist(),seed_std=float(a.mean(1).std(ddof=1)) if S>1 else 0.)


def aligned_force(values, ds, cfg):
    t=np.arange(1,cfg['future_steps']+1)*cfg['dt']
    rel=np.arange(0,1.2+1e-8,cfg['dt'])
    return np.stack([np.interp(rel,t-onset,curve[:,2]) for onset,curve in zip(ds['onset'],values)])


def evaluate(cfg,out,device):
    ds=load(out/'data');fits=json.loads((out/'classical_fits.json').read_text())
    predictions={};parameters={}
    for split in ['test_id','test_wait']:
        d=ds[split]
        for name,info in fits.items():
            mat=Material.from_dict(info['parameters']);z=ground_history(d['history'],mat,cfg['dt'])
            y=simulate(d['commands'],mat,cfg['plant'],cfg['dt'],
                       (d['history'][:,-1,0],d['history'][:,-1,1],z))[0]
            predictions[(name,0,split)]=y
        mat=Material.from_dict(cfg['truth'])
        predictions[('oracle',0,split)]=simulate(d['commands'],mat,cfg['plant'],cfg['dt'],
            (d['oracle_initial'][:,0],d['oracle_initial'][:,1],d['oracle_z']))[0]
        for name,cls in MODELS.items():
            for seed in cfg['seeds']:
                model=cls(cfg).to(device)
                ck=torch.load(out/'checkpoints'/f'{name}_{seed}.pt',map_location=device,weights_only=False)
                model.load_state_dict(ck['state_dict']);model.eval()
                h,u,_=tensors(d,device)
                modes=['carry','reset','freeze','no_history'] if name=='material_state' else ['carry']
                with torch.no_grad():
                    for mode in modes:
                        label=name if mode=='carry' else f'{name}_{mode}'
                        pred=model(h,u,mode=mode) if name=='material_state' else model(h,u)
                        predictions[(label,seed,split)]=pred.cpu().numpy()
                    if name=='material_state':
                        k0,k,tau=model.parameters_physical()
                        parameters[str(seed)]={'k_inf':float(k0),'k':k.cpu().tolist(),'tau':tau.cpu().tolist()}
    rows=[];summary={}
    model_names=sorted(set(k[0] for k in predictions))
    for name in model_names:
        for split in ['test_id','test_wait']:
            seeds=sorted(k[1] for k in predictions if k[0]==name and k[2]==split)
            all_metrics=[]
            for seed in seeds:
                met=episode_metrics(predictions[(name,seed,split)],ds[split]);all_metrics.append(met)
                for i in range(len(ds[split]['history'])):
                    row={'model':name,'seed':seed,'split':split,'episode_id':int(ds[split]['episode_ids'][i]),
                         'wait_s':float(ds[split]['waits'][i])}
                    row.update({k:float(v[i]) for k,v in met.items()});rows.append(row)
            summary[f'{name}/{split}']={k:bootstrap(np.stack([m[k] for m in all_metrics])) for k in all_metrics[0]}
    with (out/'per_episode_metrics.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    effects={}
    truth_effect=aligned_force(ds['test_wait']['truth'],ds['test_wait'],cfg)-aligned_force(ds['test_id']['truth'],ds['test_id'],cfg)
    for name in model_names:
        errors=[]
        for seed in sorted(k[1] for k in predictions if k[0]==name and k[2]=='test_id'):
            effect=aligned_force(predictions[(name,seed,'test_wait')],ds['test_wait'],cfg)-aligned_force(predictions[(name,seed,'test_id')],ds['test_id'],cfg)
            errors.append(np.sqrt(((effect-truth_effect)**2).mean(1)))
        effects[name]=bootstrap(np.stack(errors))
    effects['zero_effect_baseline']=bootstrap(np.sqrt((truth_effect**2).mean(1))[None])
    write_json(out/'summary.json',summary);write_json(out/'wait_effect.json',effects)
    write_json(out/'learned_parameters.json',parameters)
    np.savez_compressed(out/'predictions.npz',**{'__'.join(map(str,k)):v for k,v in predictions.items()})
    run_costs=[json.loads(p.read_text()) for p in sorted((out/'logs').glob('*_meta.json'))]
    write_json(out/'cost_summary.json',{
        'completed_neural_runs':len(run_costs),
        'summed_training_validation_checkpoint_wall_seconds':sum(r['seconds'] for r in run_costs),
        'maximum_pytorch_allocated_MiB':max(r['peak_allocated_MiB'] or 0 for r in run_costs),
        'memory_scope':'PyTorch allocated tensors, excluding CUDA context, display, and other processes.',
        'timing_scope':'Measured per-run wall time, not kernel-active GPU time; excludes setup and evaluation.',
        'runs':run_costs})
    make_figures(cfg,out,ds,predictions,summary,effects)
    print('RESULT',json.dumps({k:v['force_rmse_N'] for k,v in summary.items() if k.endswith('/test_wait')}),flush=True)
    source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in ROOT.glob('*.py')}
    write_json(out/'source_hashes.json',source_hashes)


def make_figures(cfg,out,ds,predictions,summary,effects):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'savefig.dpi':180,'figure.dpi':120,'axes.grid':True,'grid.alpha':.18})
    fd=out/'figures';fd.mkdir(exist_ok=True)
    colors={'classical_0':'#9b9b9b','classical_1':'#c49a00','classical_2':'#2c8a58',
            'gru_force':'#dd7858','material_state':'#466cca','material_snapshot':'#9268ae'}
    labels={'classical_0':'Elastic fit','classical_1':'1-mode Maxwell fit','classical_2':'2-mode Maxwell fit',
            'gru_force':'GRU + actuator','material_state':'Learned material state',
            'material_snapshot':'Snapshot + material'}
    names=[n for n in colors if f'{n}/test_id' in summary]
    fig,axs=plt.subplots(1,2,figsize=(12,4.5))
    for ax,metric,title in zip(axs,['force_rmse_N','position_rmse_mm'],['Recontact force RMSE (N)','Recontact position RMSE (mm)']):
        for offset,split,alpha in [(-.17,'test_id',.45),(.17,'test_wait',1.)]:
            vals=[summary[f'{n}/{split}'][metric] for n in names]
            means=np.array([v['mean'] for v in vals]);low=[v['ci_low'] for v in vals];hi=[v['ci_high'] for v in vals]
            ax.bar(np.arange(len(names))+offset,means,.32,color=[colors[n] for n in names],alpha=alpha,
                   label='ID waits' if split=='test_id' else 'Held-out waits',
                   yerr=[means-np.array(low),np.array(hi)-means],capsize=2)
        ax.set_xticks(range(len(names)),[labels[n].replace(' ','\n',1) for n in names],fontsize=8)
        ax.set_ylabel(title);ax.set_yscale('log');ax.legend(frameon=False)
    fig.suptitle('Command-conditioned, open-loop prediction | equal forecast duration\nBars: mean episode RMSE; intervals: seed + episode bootstrap',fontsize=12)
    fig.tight_layout();fig.savefig(fd/'01_main_results.png');plt.close(fig)

    fig,axs=plt.subplots(3,1,figsize=(11,8),sharex=True)
    d=ds['test_wait'];i=0;seed=cfg['seeds'][0]
    t=np.arange(1,cfg['future_steps']+1)*cfg['dt']
    axs[0].plot(t,d['commands'][i]*1000,'k--',label='Future command')
    axs[0].plot(t,d['truth'][i,:,0]*1000,'k',label='Actual motion')
    axs[1].plot(t,d['truth'][i,:,2],'k',lw=2,label='True force')
    for n in [n for n in ['classical_2','gru_force','material_state'] if n in names]:
        p=predictions[(n,0 if n.startswith('classical') else seed,'test_wait')][i]
        axs[0].plot(t,p[:,0]*1000,color=colors[n],alpha=.8,label=labels[n])
        axs[1].plot(t,p[:,2],color=colors[n],label=labels[n])
        axs[2].plot(t,p[:,2]-d['truth'][i,:,2],color=colors[n],label=labels[n])
    for ax in axs:
        ax.axvspan(.3,d['onset'][i],color='#ece9dd',alpha=.55)
        ax.axvspan(d['onset'][i],d['onset'][i]+1.2,color='#e2edf3',alpha=.35)
    axs[0].set_ylabel('Position (mm)');axs[1].set_ylabel('Force (N)');axs[2].set_ylabel('Force error (N)')
    axs[2].set_xlabel('Time after forecast cut (s)');axs[0].legend(ncol=3,fontsize=8,frameon=False)
    axs[1].legend(ncol=2,fontsize=8,frameon=False)
    axs[0].set_title(f'Predeclared example: first held-out episode, seed {seed}, wait {d["waits"][i]:.2f} s\nNo future sensor assimilation; tan = commanded wait; blue = scored window')
    fig.tight_layout();fig.savefig(fd/'02_open_loop_example.png');plt.close(fig)

    fig,axs=plt.subplots(1,2,figsize=(12,4.5))
    ab=['material_state','material_state_freeze','material_state_reset','material_state_no_history']
    if 'material_state' in names:
        vals=[summary[f'{n}/test_wait']['force_rmse_N'] for n in ab]
        means=np.array([v['mean'] for v in vals])
        axs[0].bar(range(4),means,color=['#466cca','#a398c8','#d28072','#9b9b9b'],
                   yerr=[means-np.array([v['ci_low'] for v in vals]),np.array([v['ci_high'] for v in vals])-means],capsize=3)
        axs[0].set_xticks(range(4),['Evolve','Freeze\non separation','Reset\non separation','Zero state\nat forecast cut'])
        axs[0].set_ylabel('Held-out recontact force RMSE (N)');axs[0].set_title('Inference interventions; same trained weights')
    else:
        axs[0].text(.5,.5,'Material-state interventions not evaluated',ha='center',va='center')
        axs[0].set_axis_off()
    ens=[n for n in ['classical_2','gru_force','material_state','material_snapshot'] if n in names]
    values=np.array([effects[n]['mean'] for n in ens])
    axs[1].bar(range(len(ens)),values,color=[colors[n] for n in ens],
               yerr=[values-np.array([effects[n]['ci_low'] for n in ens]),
                     np.array([effects[n]['ci_high'] for n in ens])-values],capsize=3)
    axs[1].axhline(effects['zero_effect_baseline']['mean'],color='k',ls='--',label='Predict no wait effect')
    axs[1].set_xticks(range(len(ens)),[labels[n].replace(' ','\n',1) for n in ens],fontsize=8)
    axs[1].set_ylabel('Paired wait-effect prediction RMSE (N)');axs[1].legend(fontsize=8,frameon=False)
    axs[1].set_title('Same past + same repress command, different waits')
    fig.tight_layout();fig.savefig(fd/'03_memory_and_wait_effect.png');plt.close(fig)

    learned_names=[n for n in ['material_state','gru_force','material_snapshot'] if n in names]
    fig,axs=plt.subplots(1,len(learned_names),figsize=(4.3*len(learned_names),4),squeeze=False)
    for ax,name in zip(axs[0],learned_names):
        for seed in cfg['seeds']:
            logs=json.loads((out/'logs'/f'{name}_{seed}.json').read_text())
            ax.plot([r['step'] for r in logs],[r['val_loss'] for r in logs],label=f'seed {seed}')
        ax.set_title(labels[name]);ax.set_xlabel('Optimizer updates');ax.set_ylabel('ID validation loss');ax.set_yscale('log');ax.legend(frameon=False)
    fig.tight_layout();fig.savefig(fd/'04_learning_curves.png');plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=['prepare','train','evaluate','all'])
    parser.add_argument('--config',default=str(ROOT/'config.json'))
    parser.add_argument('--output',default=str(ROOT/'runs'/'pilot_v1'))
    parser.add_argument('--device',default='cuda',choices=['cuda','cpu'])
    parser.add_argument('--models',nargs='+',choices=list(MODELS),help='Restrict profile/train/evaluation to named learned models.')
    parser.add_argument('--steps',type=int,help='Replay a fixed update count; profiling is still recorded.')
    args=parser.parse_args();cfg=json.loads(Path(args.config).read_text())
    if args.steps is not None:
        if args.steps <= 0: raise ValueError('steps must be positive')
        cfg['fixed_steps']=args.steps
    if args.models:
        for key in list(MODELS):
            if key not in args.models: del MODELS[key]
    out=Path(args.output).resolve()
    if not out.is_relative_to(ROOT): raise ValueError('Outputs must remain inside this project.')
    out.mkdir(parents=True,exist_ok=True)
    if args.device=='cuda' and not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable; explicit CPU opt-in required.')
    set_seed(0)
    if args.stage in ['prepare','all']:prepare(cfg,out,args.device)
    if args.stage in ['train','all']:train(cfg,out,args.device)
    if args.stage in ['evaluate','all']:evaluate(cfg,out,args.device)


if __name__=='__main__':main()

import hashlib,json,time
from pathlib import Path
import numpy as np
import torch
from actions import response_metrics,select,outcomes,run_reactive
from dataset import histories,test_branches,load
from dynamics import simulate
from physics_base import Material,ground_history,local_contact_observer
from models import make_model,MODEL_NAMES
from experiment import save,seed_all,ROOT


def tune_reactive(cfg,out):
    d=load(out/'data','val');d={k:v[:24] for k,v in d.items() if k in ['history','initial','z','pair_ids']}
    records=[]
    for speed in [.02,.05]:
        for buffer in [.05,.15,.30]:
            p=dict(speed=speed,buffer=buffer,gain=.02)
            r=run_reactive(cfg,d,cfg['controllers_train'],[.1,.6,1.6],cfg['force_limits'],p)
            records.append(dict(**p,cost=float(r['cost'].mean()),unsafe=float(r['unsafe'].mean()),success=float(r['success'].mean())))
    # Safety is selected on validation only; if none meet 1%, use lowest violation.
    acceptable=[r for r in records if r['unsafe']<=.01]
    best=min(acceptable,key=lambda r:r['cost']) if acceptable else min(records,key=lambda r:(r['unsafe'],r['cost']))
    save(out/'reactive_validation.json',dict(candidates=records,selected=best,selection='min cost among <=1% unsafe; otherwise min unsafe then cost',validation_pairs=24))
    return {k:best[k] for k in ['speed','buffer','gain']}


def build_context(cfg,d):
    u,ctrl=test_branches(cfg,d);shape=u.shape[:-1];N,M,C,W,A=shape
    h=np.broadcast_to(d['history'][:,:,None,None,None],(*shape,*d['history'].shape[-2:])).reshape(-1,*d['history'].shape[-2:])
    initial=np.broadcast_to(d['initial'][:,:,None,None,None],(*shape,2)).reshape(-1,2).copy()
    z=np.broadcast_to(d['z'][:,:,None,None,None],(*shape,2)).reshape(-1,2).copy()
    onsets=.3+np.array(cfg['test_waits'])[:,None]+np.array([a['extra_wait'] for a in cfg['actions']])[None,:]
    onsets=np.broadcast_to(onsets[None,None,None],shape).reshape(-1).copy()
    return dict(shape=shape,h=h,u=u.reshape(-1,u.shape[-1]),ctrl=ctrl.reshape(-1,2),initial=initial,z=z,onsets=onsets)


def model_state(cfg,out,d,name,seed):
    mat=json.loads((ROOT/'fixed_material.json').read_text())['parameters'];h=d['history'].reshape(-1,*d['history'].shape[-2:])
    if name=='oracle':return d['z'].reshape(-1,2),None
    if name=='classical_integral':return ground_history(h,Material.from_dict(mat),cfg['dt']),None
    if name=='local_observer':return local_contact_observer(h,Material.from_dict(mat),cfg['dt']),None
    base='history_state' if name in ['state_swap','state_average'] else name
    model=make_model(base,cfg,mat).cuda();ck=torch.load(out/'checkpoints'/f'{base}_{seed}_best.pt',map_location='cuda',weights_only=False)
    model.load_state_dict(ck['model']);model.eval()
    if base=='gru_contact':return None,model
    with torch.no_grad():z=model.state(torch.tensor(h,device='cuda')).cpu().numpy()
    if name=='state_swap':z=z.reshape(-1,2,2)[:,::-1].copy().reshape(-1,2)
    if name=='state_average':z=np.repeat(z.reshape(-1,2,2).mean(1)[:,None],2,axis=1).reshape(-1,2)
    return z,model


def predict(cfg,out,d,context,name,seed):
    mat=json.loads((ROOT/'fixed_material.json').read_text())['parameters'];z,model=model_state(cfg,out,d,name,seed)
    shape=context['shape'];u=context['u'];ctrl=context['ctrl']
    if name=='oracle':return simulate(context['z'],context['initial'],u,ctrl,cfg['truth'],cfg),z
    if z is not None:
        zfull=np.broadcast_to(z.reshape(shape[0],2,1,1,1,2),(*shape,2)).reshape(-1,2).copy()
        initial=context['h'][:,-1,:2].astype(float)
        return simulate(zfull,initial,u,ctrl,mat,cfg),z
    predictions=[]
    with torch.no_grad():
        for i in range(0,len(u),64):
            h=torch.tensor(context['h'][i:i+64].copy(),device='cuda')
            pred=model(h,torch.tensor(u[i:i+64],device='cuda'),torch.tensor(ctrl[i:i+64],device='cuda'))
            predictions.append(pred.cpu().numpy())
    return np.concatenate(predictions),None


def summary_metrics(cfg,context,pred,truth):
    shape=context['shape'];T=pred.shape[1];p=pred.reshape(*shape,T,3);t=truth.reshape(*shape,T,3)
    err=p-t;time,peak=response_metrics(pred,context['onsets'],cfg['dt'],cfg['goal_position'],cfg['goal_hold_seconds'])
    diff=p[:,1,...,2]-p[:,0,...,2];true_diff=t[:,1,...,2]-t[:,0,...,2]
    return dict(force_mse=np.mean(err[...,2]**2,-1),position_mse=np.mean(err[...,0]**2,-1),
                contrast_mse=np.mean((diff-true_diff)**2,-1),contrast_signal=np.mean(true_diff**2,-1),
                time=time.reshape(shape),peak=peak.reshape(shape))


def decision_metrics(cfg,m,truth):
    records={k:[] for k in ['choice','success','unsafe','reject','cost','time','peak']}
    for cap in cfg['force_limits']:
        choice=select(m['time'],m['peak'],cap,cfg['planning_force_margin'])
        r=outcomes(choice,truth['time'],truth['peak'],cap,cfg['future_seconds'])
        for k in records:records[k].append(r[k])
    return {k:np.stack(v,axis=-1) for k,v in records.items()}


def evaluate(cfg,out):
    seed_all(0);start=time.perf_counter()
    # Refuse to evaluate learned models that have not met validation convergence.
    metas=[json.loads((out/'logs'/f'{name}_{s}_meta.json').read_text()) for name in MODEL_NAMES for s in cfg['seeds']]
    if not all(m['converged'] for m in metas):raise RuntimeError('Complete validation convergence before test evaluation')
    reactive=tune_reactive(cfg,out)
    path=out/'data'/'test_histories.npz'
    if path.exists():d=dict(np.load(path))
    else:d=histories(cfg,'test');np.savez_compressed(path,**d)
    context=build_context(cfg,d);truth,_=predict(cfg,out,d,context,'oracle',0);tm=summary_metrics(cfg,context,truth,truth)
    (out/'metrics').mkdir(exist_ok=True);np.savez_compressed(out/'metrics'/'truth.npz',**tm)
    # Save only compact per-trajectory scores; full synchronized traces regenerated by cases.py.
    jobs=[('oracle',0),('classical_integral',0),('local_observer',0)]
    jobs += [(n,s) for n in MODEL_NAMES for s in cfg['seeds']]
    jobs += [(n,s) for n in ['state_swap','state_average'] for s in cfg['seeds']]
    summary=[]
    for name,seed in jobs:
        now=time.perf_counter();pred,z=predict(cfg,out,d,context,name,seed);m=summary_metrics(cfg,context,pred,truth)
        dm=decision_metrics(cfg,m,tm);result={**m,**{'decision_'+k:v for k,v in dm.items()}}
        if z is not None:result['grounded_state']=z.reshape(-1,2,2)
        np.savez_compressed(out/'metrics'/f'{name}_{seed}.npz',**result)
        unseen=slice(4,None)
        row=dict(model=name,seed=seed,force_rmse=float(np.sqrt(m['force_mse'][:,:,unseen].mean())),
                 position_rmse_mm=float(1000*np.sqrt(m['position_mse'][:,:,unseen].mean())),
                 contrast_nrmse=float(np.sqrt(m['contrast_mse'][:,unseen].sum()/m['contrast_signal'][:,unseen].sum())),
                 success=float(dm['success'][:,:,unseen].mean()),unsafe=float(dm['unsafe'][:,:,unseen].mean()),
                 reject=float(dm['reject'][:,:,unseen].mean()),cost=float(dm['cost'][:,:,unseen].mean()),seconds=time.perf_counter()-now)
        summary.append(row);print('EVAL',json.dumps(row),flush=True)
    rr=run_reactive(cfg,d,cfg['controllers_test'],cfg['test_waits'],cfg['force_limits'],reactive)
    np.savez_compressed(out/'metrics'/'reactive_0.npz',**{'decision_'+k:v for k,v in rr.items()})
    save(out/'summary.json',dict(rows=summary,reactive={k:float(v[:,:,4:].mean()) for k,v in rr.items() if k in ['success','unsafe','cost']},
        seconds=time.perf_counter()-start,test_pairs=len(d['history']),test_branches=int(np.prod(context['shape'])),
        test_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),unit='whole history pair, shared controller/action/wait branches'))
    print('EVALUATION_COMPLETE',time.perf_counter()-start,flush=True)


if __name__=='__main__':
    cfg=json.loads((ROOT/'config.json').read_text());evaluate(cfg,ROOT/'runs'/'transfer_v1')

"""Matched present observations; physical histories are replayed, never state-spliced."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.linalg import null_space
from physics_base import Material,simulate


def history_pair(cfg, seed):
    rng=np.random.default_rng(seed)
    dt=cfg['dt'];t=np.arange(round(cfg['history_seconds']/dt)+1)*dt
    mat=Material.from_dict(cfg['truth']);p=cfg['plant']
    target=rng.uniform(.0045,.0075)
    base=np.interp(t,[0,.3,.8,1.1,1.8,2.5,3.],
                   [-.004,-.004,target,target,target*rng.uniform(.9,1.1),target,target])
    centers=[rng.uniform(1.3,1.7),rng.uniform(2.0,2.4),rng.uniform(2.55,2.75),2.9,2.96,2.98]
    widths=[rng.uniform(.18,.3),rng.uniform(.12,.25),rng.uniform(.07,.14),.04,.01,.01]
    bases=np.stack([np.exp(-((t-c)/w)**2) for c,w in zip(centers,widths)])
    bases[:,t<=1.1]=0.;bases[:,-1]=0.
    eps=1e-5
    cmds=np.concatenate([base[None],base[None]+eps*bases])
    ys,zs,_,_=simulate(cmds,mat,p,dt)
    J=(ys[1:,-1]-ys[0,-1]).T/eps
    Jz=(zs[1:,-1]-zs[0,-1]).T/eps
    N=null_space(J/np.array([.006,.02,8.])[:,None])
    _,_,vt=np.linalg.svd(Jz@N)
    # Randomize null-space directions, while keeping a nonzero alias component.
    w=vt[0]+rng.normal(0,.20,N.shape[1])
    perturb=(N@w)@bases
    perturb*=rng.uniform(.0012,.0024)/np.max(np.abs(perturb))
    perturb*=rng.choice([-1.,1.])
    # Constrain the past perturbation to a feasible contact regime; keep every
    # seed. This uses only history feasibility, never future response strength.
    for shrink in range(8):
        commands=np.stack([base+perturb,base-perturb])
        y,z,c,e=simulate(commands,mat,p,dt)
        diff=np.abs(y[0,-1]-y[1,-1])
        if np.all(diff<=np.array([1e-10,1e-9,1e-7])) and np.all(c[:,t>1.1]):break
        perturb*=.5
    else:raise RuntimeError(f'Infeasible history pair {seed}, no seed discarded')
    return commands,y,z,c,e,shrink


def future_commands(cfg,seed,wait,current_u):
    rng=np.random.default_rng(seed+2000000)
    dt=cfg['dt'];t=np.arange(1,round(cfg['future_seconds']/dt)+1)*dt
    onset=.3+wait;ramp=rng.uniform(.25,.5);depth=rng.uniform(.0035,.0075)
    u=np.interp(t,[0,.3,onset,onset+ramp,cfg['future_seconds']],
                [current_u,-.004,-.004,depth,depth])
    return u,(t>=onset)&(t<=onset+1.2),onset


def split(cfg,seeds,waits):
    data={k:[] for k in ['history','commands','labels','truth','oracle_z','oracle_initial',
                         'full_observed','full_commands','metric_mask','onset','waits','pair_ids',
                         'endpoint_mismatch','truth_contact','construction_shrink_count']}
    sig=np.array([cfg['sensor_std'][k] for k in ['position','velocity','force']])
    mat=Material.from_dict(cfg['truth'])
    for seed,wait in zip(seeds,waits):
        hu,hy,hz,hc,he,shrink=history_pair(cfg,int(seed))
        fu,mask,onset=future_commands(cfg,int(seed),wait,hu[0,-1])
        future=np.repeat(fu[None],2,axis=0)
        fy,fz,fc,fe=simulate(future,mat,cfg['plant'],cfg['dt'],(hy[:,-1,0],hy[:,-1,1],hz[:,-1]))
        rng=np.random.default_rng(int(seed)+1000000)
        observed=hy+rng.normal(size=hy.shape)*sig
        # Matched endpoint plus common noise: snapshot inputs are byte-identical.
        common=hy[:,-1].mean(0)+rng.normal(size=3)*sig
        observed[:,-1]=common
        noisy_future=fy+rng.normal(size=fy.shape)*sig
        hist=np.concatenate([observed,hu[...,None],np.full((*hu.shape,1),cfg['dt'])],-1)
        values=dict(history=hist.astype('float32'),commands=future.astype('float32'),
                    labels=noisy_future.astype('float32'),truth=fy,oracle_z=hz[:,-1],
                    oracle_initial=hy[:,-1,:2],full_observed=np.concatenate([observed,noisy_future],1),
                    full_commands=np.concatenate([hu,future],1),metric_mask=mask,onset=onset,waits=wait,
                    pair_ids=seed,endpoint_mismatch=np.abs(hy[0,-1]-hy[1,-1]),truth_contact=fc,
                    construction_shrink_count=shrink)
        for k,v in values.items():data[k].append(v)
    return {k:np.asarray(v) for k,v in data.items()}


def generate(cfg,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(cfg['data_seed'])
    ds={}
    for name,n,offset in [('train',cfg['train_pairs'],0),('val',cfg['val_pairs'],10000),
                           ('test_id',cfg['test_pairs'],20000)]:
        ranges=np.asarray(cfg['train_wait_ranges'])
        selected=ranges[rng.integers(0,len(ranges),n)]
        seeds=cfg['data_seed']+offset+np.arange(n)
        ds[name]=split(cfg,seeds,rng.uniform(selected[:,0],selected[:,1]))
        print('DATA',name,n,'pairs',flush=True)
    ds['test_wait']=split(cfg,ds['test_id']['pair_ids'],rng.uniform(*cfg['test_wait_range'],cfg['test_pairs']))
    manifest={'config':cfg,'splits':{},'pair_axis':'N,2,...; entire pair remains in one partition',
              'privileged':['truth','oracle_z','oracle_initial','truth_contact'],
              'pair_construction':'Null-space command perturbations, replayed from a relaxed initial state.',
              'noise':'Independent history/future noise except shared endpoint noise within a pair.',
              'selection':'All seeds retained. Past perturbation halved if needed to maintain endpoint/contact feasibility; counts recorded. No future-effect filtering.'}
    for name,d in ds.items():
        assert np.array_equal(d['history'][:,0,-1],d['history'][:,1,-1])
        path=out/f'{name}.npz';np.savez_compressed(path,**d)
        manifest['splits'][name]={'pairs':len(d['history']),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'endpoint_max_difference':d['endpoint_mismatch'].max(0).tolist()}
    assert np.array_equal(ds['test_id']['history'],ds['test_wait']['history'])
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return ds


def load(path):
    return {n:dict(np.load(Path(path)/f'{n}.npz')) for n in ['train','val','test_id','test_wait']}


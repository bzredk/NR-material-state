"""New histories; every future branch shares the same physically replayed state."""
import hashlib,json
from pathlib import Path
import numpy as np
from paired_history import history_pair
from dynamics import simulate


def command(cfg,current,wait,ramp,depth):
    t=np.arange(1,round(cfg['future_seconds']/cfg['dt'])+1)*cfg['dt']
    return np.interp(t,[0,.3,.3+wait,.3+wait+ramp,cfg['future_seconds']],
                    [current,-.004,-.004,depth,depth])


def histories(cfg,name):
    n=cfg[name+'_pairs'];offset={'train':300000,'val':310000,'test':320000}[name]
    sig=np.array([cfg['sensor_std'][k] for k in ['position','velocity','force']]);items=[]
    for j in range(n):
        seed=cfg['data_seed']+offset+j;hu,hy,hz,hc,he,shrink=history_pair(cfg,seed)
        rng=np.random.default_rng(seed+5000000);obs=hy+rng.normal(size=hy.shape)*sig
        obs[:,-1]=hy[:,-1].mean(0)+rng.normal(size=3)*sig
        h=np.concatenate([obs,hu[...,None],np.full((*hu.shape,1),cfg['dt'])],-1)
        items.append((h,hy[:,-1,:2],hz[:,-1],seed,shrink,np.abs(hy[0,-1]-hy[1,-1])))
    d={k:np.asarray([it[i] for it in items]) for i,k in enumerate(['history','initial','z','pair_ids','shrink','endpoint_mismatch'])}
    d['history']=d['history'].astype('float32');return d


def training_branches(cfg,d,single=False):
    n=len(d['history']);T=round(cfg['future_seconds']/cfg['dt']);u=np.empty((n,4,2,T))
    ctr=np.empty((n,4,2,2));sig=np.array([cfg['sensor_std'][k] for k in ['position','velocity','force']])
    for j,seed in enumerate(d['pair_ids']):
        rng=np.random.default_rng(int(seed)+6000000)
        for b in range(4):
            u[j,b]=command(cfg,d['history'][j,0,-1,3],rng.uniform(.1,2.4),rng.uniform(.12,1.7),rng.uniform(.0065,.0085))
            ctr[j,b]=cfg['controllers_train'][0 if single else b]
    initial=np.broadcast_to(d['initial'][:,None],(n,4,2,2)).reshape(-1,2)
    z=np.broadcast_to(d['z'][:,None],(n,4,2,2)).reshape(-1,2)
    y=simulate(z,initial,u.reshape(-1,T),ctr.reshape(-1,2),cfg['truth'],cfg).reshape(n,4,2,T,3)
    rng=np.random.default_rng(int(d['pair_ids'][0])+7000000);label=y+rng.normal(size=y.shape)*sig
    return dict(commands=u.astype('float32'),controls=ctr.astype('float32'),labels=label.astype('float32'))


def prepare(cfg,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);manifest={}
    for name in ['train','val']:
        d=histories(cfg,name);multi=training_branches(cfg,d);single=training_branches(cfg,d,True)
        path=out/f'{name}.npz';np.savez_compressed(path,**d,**multi,single_labels=single['labels'])
        manifest[name]={'pairs':len(d['history']),'future_branches_per_history':4,
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'ids':d['pair_ids'].tolist()}
        print('DATA',name,len(d['history']),flush=True)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')


def test_branches(cfg,d):
    N=len(d['history']);C=len(cfg['controllers_test']);W=len(cfg['test_waits']);A=len(cfg['actions'])
    T=round(cfg['future_seconds']/cfg['dt']);shape=(N,2,C,W,A)
    u=np.empty((*shape,T),np.float32);ctrl=np.empty((*shape,2),np.float32)
    for n in range(N):
        for c,control in enumerate(cfg['controllers_test']):
            for w,wait in enumerate(cfg['test_waits']):
                for a,action in enumerate(cfg['actions']):
                    u[n,:,c,w,a]=command(cfg,d['history'][n,0,-1,3],wait+action['extra_wait'],action['ramp'],action.get('depth',cfg['action_depth']))
                    ctrl[n,:,c,w,a]=control
    return u,ctrl


def load(out,name):return dict(np.load(Path(out)/f'{name}.npz'))

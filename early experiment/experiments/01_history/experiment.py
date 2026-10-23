import os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import argparse,hashlib,json,platform,random,time
import numpy as np
import scipy
from scipy.optimize import least_squares
import torch
from data import generate,load
from physics import Material,observe_force_from_positions
from models import make_model,MODEL_NAMES,loss


def save(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')


def seed_all(seed):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed);torch.backends.cudnn.benchmark=False
    torch.backends.cudnn.deterministic=True;torch.set_num_threads(1)


def flatten(d,key):
    a=d[key];return a.reshape(-1,*a.shape[2:])


def tensor_data(d,device):
    return tuple(torch.tensor(flatten(d,k),device=device) for k in ['history','commands','labels'])


def fit_material(cfg,d):
    xs=flatten(d,'full_observed')[...,0];fs=flatten(d,'full_observed')[...,2]
    def unpack(lp):
        p=np.exp(lp);return Material(p[0],p[1:3],p[3:])
    def res(lp):
        return ((observe_force_from_positions(xs,unpack(lp),cfg['dt'])-fs)/8.).ravel()
    start=time.perf_counter()
    result=least_squares(res,np.log([600.,700.,1000.,.25,2.]),
        bounds=(np.log([20.,20.,20.,.02,.02]),np.log([10000.,10000.,10000.,10.,10.])),
        max_nfev=100,ftol=1e-9,xtol=1e-9,gtol=1e-9)
    mat=unpack(result.x);idx=np.argsort(mat.tau);mat.k=mat.k[idx];mat.tau=mat.tau[idx]
    return dict(parameters=mat.as_dict(),seconds=time.perf_counter()-start,success=bool(result.success),
                nfev=result.nfev,source='round2 TRAIN measured position and force; all later parameters frozen')


def prepare(cfg,out):
    start=time.perf_counter();ds=generate(cfg,out/'data')
    save(out/'config.json',cfg)
    fit=fit_material(cfg,ds['train']);save(out/'fixed_material.json',fit)
    print('FIXED_MATERIAL',json.dumps(fit),flush=True)
    save(out/'environment.json',dict(python=platform.python_version(),torch=torch.__version__,
       numpy=np.__version__,scipy=scipy.__version__,gpu=torch.cuda.get_device_name(),
       cuda=torch.version.cuda,total_memory_GiB=torch.cuda.get_device_properties(0).total_memory/2**30,
       preparation_seconds=time.perf_counter()-start,physics_engine='NumPy exact branchwise adjoint; GRUs on CUDA'))
    h,u,y=tensor_data(ds['train'],'cuda');profile={}
    for name in MODEL_NAMES:
        seed_all(0);model=make_model(name,cfg,fit['parameters']).cuda()
        opt=torch.optim.Adam(model.parameters(),lr=cfg['learning_rate']);times=[]
        torch.cuda.reset_peak_memory_stats()
        for k in range(5):
            torch.cuda.synchronize();t=time.perf_counter();opt.zero_grad(set_to_none=True)
            pred=model(h[:64],u[:64]);value=loss(pred,y[:64]);value.backward();opt.step()
            torch.cuda.synchronize()
            if k>=2:times.append(time.perf_counter()-t)
        profile[name]=dict(seconds_per_update=float(np.median(times)),
           parameters=sum(p.numel() for p in model.parameters()),peak_pytorch_allocated_MiB=torch.cuda.max_memory_allocated()/2**20)
        print('PROFILE',name,json.dumps(profile[name]),flush=True)
    save(out/'profile.json',profile)
    save(out/'source_hashes_before_training.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')})


def validation(model,h,u,y,batch=64):
    model.eval();s=0.
    with torch.no_grad():
        for i in range(0,len(h),batch):
            n=min(batch,len(h)-i);s+=float(loss(model(h[i:i+n],u[i:i+n]),y[i:i+n]))*n
    return s/len(h)


def train(cfg,out,names=None,seeds=None,resume=False):
    ds=load(out/'data');mat=json.loads((out/'fixed_material.json').read_text())['parameters']
    th,tu,ty=tensor_data(ds['train'],'cuda');vh,vu,vy=tensor_data(ds['val'],'cuda')
    for name in names or MODEL_NAMES:
        for seed in seeds or cfg['seeds']:
            stem=f'{name}_{seed}';meta_path=out/'logs'/f'{stem}_meta.json'
            if meta_path.exists() and json.loads(meta_path.read_text()).get('converged'):
                print('SKIP_CONVERGED',stem,flush=True);continue
            seed_all(seed);model=make_model(name,cfg,mat).cuda()
            opt=torch.optim.Adam(model.parameters(),lr=cfg['learning_rate'])
            scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(opt,factor=cfg['lr_factor'],
                patience=cfg['lr_patience_evaluations'],threshold=cfg['meaningful_relative_improvement'],
                min_lr=cfg['minimum_lr'])
            logs=[];best=float('inf');significant=float('inf');last_significant=0;start_step=0;elapsed_before=0.
            rng=np.random.default_rng(seed+100)
            latest=out/'checkpoints'/f'{stem}_latest.pt'
            if resume and latest.exists():
                ck=torch.load(latest,weights_only=False,map_location='cuda')
                model.load_state_dict(ck['model']);opt.load_state_dict(ck['optimizer']);scheduler.load_state_dict(ck['scheduler'])
                best=ck['best'];significant=ck['significant'];last_significant=ck['last_significant']
                start_step=ck['step']+1;logs=ck['logs'];elapsed_before=ck['seconds'];rng.bit_generator.state=ck['rng']
            (out/'checkpoints').mkdir(exist_ok=True);(out/'logs').mkdir(exist_ok=True)
            torch.cuda.reset_peak_memory_stats();start=time.perf_counter();converged=False
            for step in range(start_step,cfg['maximum_updates']+1):
                if step>0:
                    model.train();pairs=rng.choice(len(ds['train']['history']),cfg['batch_pairs'],replace=False)
                    idx=torch.tensor((pairs[:,None]*2+np.array([0,1])).ravel(),device='cuda')
                    opt.zero_grad(set_to_none=True);value=loss(model(th[idx],tu[idx]),ty[idx])
                    if not torch.isfinite(value):raise RuntimeError(f'Nonfinite loss {stem} {step}')
                    value.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.);opt.step()
                if step%cfg['validation_interval'] and step!=cfg['maximum_updates']:continue
                val=validation(model,vh,vu,vy);scheduler.step(val)
                if val<best:
                    best=val;torch.save({'model':model.state_dict(),'step':step,'validation_loss':val,'fixed_material':mat},
                                       out/'checkpoints'/f'{stem}_best.pt')
                if val<significant*(1-cfg['meaningful_relative_improvement']):
                    significant=val;last_significant=step
                converged=(step>=cfg['minimum_updates'] and
                    step-last_significant>=cfg['plateau_evaluations']*cfg['validation_interval'])
                record=dict(step=step,val_loss=val,train_loss=float(value.detach()) if step else None,
                      learning_rate=opt.param_groups[0]['lr'],seconds=elapsed_before+time.perf_counter()-start,
                      last_significant_improvement=last_significant,converged=converged)
                logs.append(record);save(out/'logs'/f'{stem}.json',logs)
                torch.save(dict(model=model.state_dict(),optimizer=opt.state_dict(),scheduler=scheduler.state_dict(),
                    step=step,best=best,significant=significant,last_significant=last_significant,logs=logs,
                    seconds=record['seconds'],rng=rng.bit_generator.state),latest)
                print('TRAIN',stem,json.dumps(record),flush=True)
                if converged:break
            meta=dict(model=name,seed=seed,steps=step,best_val_loss=best,converged=converged,
              stop_reason='validation_plateau' if converged else 'budget_cap_not_converged',
              seconds=elapsed_before+time.perf_counter()-start,parameters=sum(p.numel() for p in model.parameters()),
              peak_pytorch_allocated_MiB=torch.cuda.max_memory_allocated()/2**20)
            save(meta_path,meta);print('COMPLETE',json.dumps(meta),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','train','evaluate','all'])
    p.add_argument('--output',default=str(ROOT/'runs'/'round2_v1'));p.add_argument('--models',nargs='+',choices=MODEL_NAMES)
    p.add_argument('--seeds',nargs='+',type=int);p.add_argument('--resume',action='store_true')
    args=p.parse_args();out=Path(args.output).resolve()
    if not out.is_relative_to(ROOT):raise ValueError('Project-local outputs required')
    out.mkdir(parents=True,exist_ok=True);cfg=json.loads((ROOT/'config.json').read_text());seed_all(0)
    if not torch.cuda.is_available():raise RuntimeError('CUDA required for this recorded experiment')
    if args.stage in ['prepare','all']:prepare(cfg,out)
    if args.stage in ['train','all']:train(cfg,out,args.models,args.seeds,args.resume)
    if args.stage in ['evaluate','all']:
        from evaluate import evaluate
        evaluate(cfg,out)


if __name__=='__main__':main()

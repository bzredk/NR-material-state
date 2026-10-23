import os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import argparse,hashlib,json,platform,random,time
import numpy as np
import scipy,torch
from dataset import prepare as prepare_data,load,histories,training_branches
from models import MODEL_NAMES,make_model,loss


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')


def seed_all(seed):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True;torch.set_num_threads(1)


def tensors(d,single=False):
    n,_,H,F=d['history'].shape
    h=np.broadcast_to(d['history'][:,None],(n,4,2,H,F)).reshape(-1,H,F).copy()
    u=d['commands'].reshape(-1,d['commands'].shape[-1]);c=d['controls'].reshape(-1,2).copy()
    if single:c[:]=[1200.,25.]
    y=d['single_labels' if single else 'labels'].reshape(-1,d['labels'].shape[-2],3)
    return [torch.tensor(v,device='cuda') for v in [h,u,c,y]]


def profile(cfg,out):
    small=dict(cfg,train_pairs=8);d=histories(small,'train');d.update(training_branches(small,d))
    d['single_labels']=d['labels'];h,u,c,y=tensors(d);material=json.loads((ROOT/'fixed_material.json').read_text())['parameters']
    results={}
    for name in ['snapshot_state','history_state','gru_contact']:
        seed_all(0);model=make_model(name,cfg,material).cuda();opt=torch.optim.Adam(model.parameters(),lr=.003)
        times=[];torch.cuda.reset_peak_memory_stats()
        for i in range(10):
            torch.cuda.synchronize();start=time.perf_counter();opt.zero_grad(set_to_none=True)
            value=loss(model(h,u,c),y);value.backward();opt.step();torch.cuda.synchronize()
            if i>=5:times.append(time.perf_counter()-start)
        results[name]={'seconds_per_update':float(np.median(times)),
          'parameters':sum(p.numel() for p in model.parameters()),'peak_allocated_MiB':torch.cuda.max_memory_allocated()/2**20}
        print('PROFILE',name,json.dumps(results[name]),flush=True)
    save(out/'profile.json',results)
    save(out/'environment.json',{'python':platform.python_version(),'torch':torch.__version__,'numpy':np.__version__,
        'scipy':scipy.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(),
        'gpu_memory_GiB':torch.cuda.get_device_properties(0).total_memory/2**30,
        'mechanics':'Numba CPU implicit solve + exact branchwise adjoints; GRUs on CUDA'})


def validation(model,data):
    h,u,c,y=data;model.eval();total=0.
    with torch.no_grad():
        for i in range(0,len(h),64):
            stop=min(i+64,len(h));total+=float(loss(model(h[i:stop],u[i:stop],c[i:stop]),y[i:stop]))*(stop-i)
    return total/len(h)


def train(cfg,out,names,seeds,resume=False):
    mat=json.loads((ROOT/'fixed_material.json').read_text())['parameters'];ds={k:load(out/'data',k) for k in ['train','val']}
    for name in names:
        tr=tensors(ds['train'],name=='history_single');va=tensors(ds['val'],name=='history_single')
        for seed in seeds:
            stem=f'{name}_{seed}';mp=out/'logs'/f'{stem}_meta.json'
            if mp.exists() and json.loads(mp.read_text())['converged']:
                print('SKIP_CONVERGED',stem,flush=True);continue
            seed_all(seed);model=make_model(name,cfg,mat).cuda();opt=torch.optim.Adam(model.parameters(),lr=cfg['learning_rate'])
            scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(opt,factor=cfg['lr_factor'],patience=cfg['lr_patience_evaluations'],
                threshold=cfg['meaningful_relative_improvement'],min_lr=cfg['minimum_lr'])
            rng=np.random.default_rng(seed+100);best=float('inf');significant=float('inf');last=0;logs=[];start_step=0;elapsed=0.
            latest=out/'checkpoints'/f'{stem}_latest.pt';latest.parent.mkdir(parents=True,exist_ok=True)
            if resume and latest.exists():
                ck=torch.load(latest,map_location='cuda',weights_only=False);model.load_state_dict(ck['model'])
                opt.load_state_dict(ck['optimizer']);scheduler.load_state_dict(ck['scheduler']);rng.bit_generator.state=ck['rng']
                best=ck['best'];significant=ck['significant'];last=ck['last'];logs=ck['logs'];start_step=ck['step']+1;elapsed=ck['seconds']
            torch.cuda.reset_peak_memory_stats();start=time.perf_counter();converged=False
            h,u,c,y=tr
            for step in range(start_step,cfg['maximum_updates']+1):
                if step:
                    model.train();p=rng.choice(len(ds['train']['history']),cfg['batch_pairs'],replace=False);b=rng.integers(0,4,len(p))
                    idx=torch.tensor(((p[:,None]*4+b[:,None])*2+np.array([0,1])).ravel(),device='cuda')
                    opt.zero_grad(set_to_none=True);value=loss(model(h[idx],u[idx],c[idx]),y[idx])
                    if not torch.isfinite(value):raise RuntimeError(f'Nonfinite loss {stem}:{step}')
                    value.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.);opt.step()
                if step%cfg['validation_interval'] and step!=cfg['maximum_updates']:continue
                val=validation(model,va);scheduler.step(val)
                if val<best:
                    best=val;torch.save({'model':model.state_dict(),'step':step,'validation_loss':val},out/'checkpoints'/f'{stem}_best.pt')
                if val<significant*(1-cfg['meaningful_relative_improvement']):significant=val;last=step
                converged=step>=cfg['minimum_updates'] and step-last>=cfg['plateau_evaluations']*cfg['validation_interval']
                record=dict(step=step,val_loss=val,train_loss=float(value.detach()) if step else None,
                            learning_rate=opt.param_groups[0]['lr'],seconds=elapsed+time.perf_counter()-start,converged=converged,last_improvement=last)
                logs.append(record);save(out/'logs'/f'{stem}.json',logs)
                torch.save(dict(model=model.state_dict(),optimizer=opt.state_dict(),scheduler=scheduler.state_dict(),rng=rng.bit_generator.state,
                    best=best,significant=significant,last=last,logs=logs,step=step,seconds=record['seconds']),latest)
                print('TRAIN',stem,json.dumps(record),flush=True)
                if converged:break
            meta=dict(model=name,seed=seed,steps=step,best_val_loss=best,converged=converged,
               stop_reason='validation_plateau' if converged else 'budget_cap_not_converged',seconds=elapsed+time.perf_counter()-start,
               parameters=sum(p.numel() for p in model.parameters()),peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20)
            save(mp,meta);print('COMPLETE',json.dumps(meta),flush=True)
        del tr,va


def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['profile','prepare','train','evaluate','all'])
    parser.add_argument('--models',nargs='+',default=MODEL_NAMES);parser.add_argument('--seeds',nargs='+',type=int,default=None)
    parser.add_argument('--resume',action='store_true');args=parser.parse_args();cfg=json.loads((ROOT/'config.json').read_text())
    out=ROOT/'runs'/'transfer_v2';out.mkdir(parents=True,exist_ok=True);seed_all(0)
    if args.stage in ['profile','all']:profile(cfg,out)
    if args.stage in ['prepare','all']:
        start=time.perf_counter();prepare_data(cfg,out/'data');save(out/'config.json',cfg)
        save(out/'preparation.json',{'seconds':time.perf_counter()-start})
        save(out/'source_hashes_before_training.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')})
    if args.stage in ['train','all']:train(cfg,out,args.models,args.seeds or cfg['seeds'],args.resume)
    if args.stage in ['evaluate','all']:
        from evaluate import evaluate
        evaluate(cfg,out)


if __name__=='__main__':main()


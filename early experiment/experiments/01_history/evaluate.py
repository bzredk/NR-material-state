import csv,hashlib,json
from pathlib import Path
import numpy as np
import torch
from data import load
from physics import Material,simulate,ground_history,local_contact_observer
from models import make_model,MODEL_NAMES
from experiment import flatten,save,seed_all


def pair_metrics(pred,d,z=None):
    mask=d['metric_mask'];n=mask.sum(-1);truth=d['truth']
    diff=pred[...,2]-truth[...,2]
    fmse=(diff**2*mask[:,None]).sum(-1)/n[:,None]
    xmse=((pred[...,0]-truth[...,0])**2*mask[:,None]).sum(-1)/n[:,None]
    actual_delta=truth[:,1,:,2]-truth[:,0,:,2]
    predicted_delta=pred[:,1,:,2]-pred[:,0,:,2]
    metrics=dict(force_rmse_N=np.sqrt(fmse).mean(1),position_rmse_mm=np.sqrt(xmse).mean(1)*1000,
        effect_error_mse=((predicted_delta-actual_delta)**2*mask).sum(-1)/n,
        effect_signal_mse=(actual_delta**2*mask).sum(-1)/n,
        effect_prediction_mse=(predicted_delta**2*mask).sum(-1)/n,
        free_force_rmse_N=np.sqrt(np.sum(pred[...,2]**2*~d['truth_contact'],axis=(1,2))/np.maximum(1,(~d['truth_contact']).sum((1,2)))))
    if z is not None:
        true_z=d['oracle_z'];normal=np.array([1300.,-900.]);normal/=np.linalg.norm(normal)
        dztrue=(true_z[:,1]-true_z[:,0])@normal
        dzpred=(z[:,1]-z[:,0])@normal
        metrics.update(state_rmse_mm=np.sqrt(((z-true_z)**2).mean((1,2)))*1000,
            contrast_error_sq=(dzpred-dztrue)**2,contrast_signal_sq=dztrue**2,
            true_contrast_m=dztrue,predicted_contrast_m=dzpred)
    return metrics


def aggregate(records,cfg):
    # records: seed x metric x pair. Paired IDs are sampled as whole units.
    arr={k:np.stack([r[k] for r in records]) for k in records[0]}
    def values(a):
        r={k:float(v.mean()) for k,v in a.items() if k in ['force_rmse_N','position_rmse_mm','free_force_rmse_N','state_rmse_mm']}
        r['paired_effect_RMSE_N']=float(np.sqrt(a['effect_error_mse'].mean()))
        r['paired_effect_NRMSE']=float(np.sqrt(a['effect_error_mse'].mean()/a['effect_signal_mse'].mean()))
        r['effect_signal_RMS_N']=float(np.sqrt(a['effect_signal_mse'].mean()))
        if 'contrast_error_sq' in a:
            r['state_contrast_NRMSE']=float(np.sqrt(a['contrast_error_sq'].mean()/a['contrast_signal_sq'].mean()))
        return r
    means=values(arr);rng=np.random.default_rng(553);S,N=next(iter(arr.values())).shape
    boots={k:[] for k in means}
    for _ in range(cfg['bootstrap_resamples']):
        si=rng.integers(0,S,S);ni=rng.integers(0,N,N)
        vs=values({k:v[si][:,ni] for k,v in arr.items()})
        for k,v in vs.items():boots[k].append(v)
    return {k:dict(mean=v,ci_low=float(np.quantile(boots[k],.025)),ci_high=float(np.quantile(boots[k],.975)),
                   seed_values=[values({kk:vv[i:i+1] for kk,vv in arr.items()})[k] for i in range(S)]) for k,v in means.items()}


def evaluate(cfg,out):
    ds=load(out/'data');fit=json.loads((out/'fixed_material.json').read_text())['parameters']
    metadata=[json.loads((out/'logs'/f'{name}_{seed}_meta.json').read_text()) for name in MODEL_NAMES for seed in cfg['seeds']]
    assert all(r['converged'] for r in metadata),'Resolve validation convergence before evaluating test performance.'
    save(out/'cost_summary.json',dict(total_training_wall_seconds=sum(r['seconds'] for r in metadata),runs=metadata,
       memory_scope='PyTorch allocations exclude NumPy arrays, CUDA context, and desktop',timing_scope='training + validation + checkpoints; not kernel-active GPU time'))
    preds={};states={};summary={};allrows=[]
    for split in ['test_id','test_wait']:
        d=ds[split];P=len(d['history']);h=flatten(d,'history');u=flatten(d,'commands')
        mat=Material.from_dict(fit);z=ground_history(h,mat,cfg['dt'])
        y=simulate(u,mat,cfg['plant'],cfg['dt'],(h[:,-1,0],h[:,-1,1],z))[0]
        preds[('classical_integral',0,split)]=y.reshape(P,2,-1,3);states[('classical_integral',0,split)]=z.reshape(P,2,2)
        local_z=local_contact_observer(h,mat,cfg['dt'])
        local_y=simulate(u,mat,cfg['plant'],cfg['dt'],(h[:,-1,0],h[:,-1,1],local_z))[0]
        preds[('local_observer',0,split)]=local_y.reshape(P,2,-1,3);states[('local_observer',0,split)]=local_z.reshape(P,2,2)
        oracle=simulate(u,Material.from_dict(cfg['truth']),cfg['plant'],cfg['dt'],
             (flatten(d,'oracle_initial')[:,0],flatten(d,'oracle_initial')[:,1],flatten(d,'oracle_z')))[0]
        preds[('oracle',0,split)]=oracle.reshape(P,2,-1,3);states[('oracle',0,split)]=d['oracle_z']
        preds[('pair_average_oracle',0,split)]=np.repeat(d['truth'].mean(1,keepdims=True),2,axis=1)
        for name in MODEL_NAMES:
            for seed in cfg['seeds']:
                seed_all(seed);model=make_model(name,cfg,fit).cuda()
                ck=torch.load(out/'checkpoints'/f'{name}_{seed}_best.pt',weights_only=False,map_location='cuda')
                model.load_state_dict(ck['model']);model.eval();outputs=[];zs=[]
                with torch.no_grad():
                    for start in range(0,len(h),64):
                        hh=torch.tensor(h[start:start+64],device='cuda');uu=torch.tensor(u[start:start+64],device='cuda')
                        outputs.append(model(hh,uu).cpu().numpy())
                        if name in ['history_state','snapshot_state']:zs.append(model.state(hh).cpu().numpy())
                preds[(name,seed,split)]=np.concatenate(outputs).reshape(P,2,-1,3)
                if zs:
                    states[(name,seed,split)]=np.concatenate(zs).reshape(P,2,2)
                if name=='history_state':
                    swapped=states[(name,seed,split)][:,::-1].reshape(-1,2)
                    sy=simulate(u,mat,cfg['plant'],cfg['dt'],(h[:,-1,0],h[:,-1,1],swapped))[0]
                    preds[('history_state_swapped',seed,split)]=sy.reshape(P,2,-1,3)
        names=sorted({key[0] for key in preds if key[2]==split})
        for name in names:
            rec=[]
            for seed in sorted(key[1] for key in preds if key[0]==name and key[2]==split):
                key=(name,seed,split);m=pair_metrics(preds[key],d,states.get(key));rec.append(m)
                for i,pid in enumerate(d['pair_ids']):
                    row=dict(model=name,seed=seed,split=split,pair_id=int(pid),wait_s=float(d['waits'][i]))
                    row.update({k:float(v[i]) for k,v in m.items()});allrows.append(row)
            summary[f'{name}/{split}']=aggregate(rec,cfg)
    save(out/'summary.json',summary)
    columns=sorted(set().union(*(set(r) for r in allrows)))
    with (out/'per_pair_metrics.csv').open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=columns);wr.writeheader();wr.writerows(allrows)
    np.savez_compressed(out/'predictions.npz',**{'__'.join(map(str,k)):v for k,v in preds.items()})
    np.savez_compressed(out/'states.npz',**{'__'.join(map(str,k)):v for k,v in states.items()})
    make_figures(cfg,out,ds,preds,states,summary)
    save(out/'source_hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')})
    print('RESULT',json.dumps({k:{m:v[m]['mean'] for m in ['paired_effect_NRMSE','force_rmse_N']} for k,v in summary.items() if k.endswith('test_wait')}),flush=True)


def make_figures(cfg,out,ds,preds,states,summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18})
    fd=out/'figures';fd.mkdir(exist_ok=True)
    colors={'classical_integral':'#27885b','local_observer':'#57a6a1','snapshot_state':'#9b79b3','history_state':'#356ac3','gru_contact':'#de833c','gru_force':'#ad5b53','history_state_swapped':'#808080'}
    labels={'classical_integral':'Classical\nintegration','local_observer':'Local 0.2 s\nobserver','snapshot_state':'Current-only\nstate','history_state':'History\nstate','gru_contact':'GRU +\ncontact','gru_force':'GRU +\nforce','history_state_swapped':'History state\nexchanged'}
    names=list(colors)[:6]
    fig,axs=plt.subplots(1,2,figsize=(12,4.6))
    for ax,metric,title in zip(axs,['paired_effect_NRMSE','force_rmse_N'],['Paired response-difference NRMSE','Recontact force RMSE (N)']):
        for off,split,alpha in [(-.17,'test_id',.45),(.17,'test_wait',1.)]:
            vals=[summary[f'{n}/{split}'][metric] for n in names];mu=np.array([v['mean'] for v in vals])
            ax.bar(np.arange(len(names))+off,mu,.32,color=[colors[n] for n in names],alpha=alpha,
               yerr=[mu-np.array([v['ci_low'] for v in vals]),np.array([v['ci_high'] for v in vals])-mu],capsize=2,
               label='ID waits' if split=='test_id' else 'Held-out waits')
        ax.set_xticks(range(len(names)),[labels[n] for n in names],fontsize=8);ax.set_ylabel(title)
        ax.set_yscale('log');ax.legend(frameon=True,facecolor='white',edgecolor='none',framealpha=1,fontsize=8)
    axs[0].axhline(1,color='k',ls='--',lw=1);axs[0].axhline(.5,color='k',ls=':',lw=1)
    fig.suptitle('Same current observations + same future commands; different physical histories\nDashed = predict no difference; dotted = predeclared useful-recovery threshold')
    fig.tight_layout();fig.savefig(fd/'01_main_results.png',dpi=180);plt.close(fig)

    d=ds['test_wait'];i=0;seed=cfg['seeds'][0];t=np.arange(1,d['commands'].shape[-1]+1)*cfg['dt']
    ht=np.arange(d['history'].shape[2])*cfg['dt'];fig,axs=plt.subplots(3,1,figsize=(11,8))
    for j in [0,1]:axs[0].plot(ht,d['history'][i,j,:,0]*1000,label=f'Past motion {"AB"[j]}')
    axs[0].set_ylabel('Position (mm)');axs[0].set_xlabel('History time (s)');axs[0].legend(frameon=False)
    axs[0].set_title('Fixed example: first test pair, no curve selection; endpoint observations identical')
    for j in [0,1]:axs[1].plot(t,d['truth'][i,j,:,2],color='k',ls='-' if j==0 else '--',label=f'True force {"AB"[j]}')
    true=d['truth'][i,1,:,2]-d['truth'][i,0,:,2];axs[2].plot(t,true,color='k',lw=2,label='True B - A')
    for n in names:
        pred=preds[(n,0 if n in ['classical_integral','local_observer'] else seed,'test_wait')]
        axs[2].plot(t,pred[i,1,:,2]-pred[i,0,:,2],color=colors[n],label=labels[n].replace('\n',' '))
    for ax in axs[1:]:ax.axvspan(d['onset'][i],d['onset'][i]+1.2,alpha=.15,color='steelblue')
    axs[1].set_ylabel('Force (N)');axs[1].legend(frameon=False,ncol=2)
    axs[2].set_ylabel('Force difference (N)');axs[2].set_xlabel('Future time (s)');axs[2].legend(frameon=False,ncol=2,fontsize=8)
    fig.tight_layout();fig.savefig(fd/'02_history_pair_and_response.png',dpi=180);plt.close(fig)

    fig,axs=plt.subplots(1,3,figsize=(13,4))
    normal=np.array([1300.,-900.]);normal/=np.linalg.norm(normal)
    truth=(d['oracle_z'][:,1]-d['oracle_z'][:,0])@normal*1000
    for ax,n in zip(axs[:2],['snapshot_state','history_state']):
        for seed in cfg['seeds']:
            z=states[(n,seed,'test_wait')];pred=(z[:,1]-z[:,0])@normal*1000
            ax.scatter(truth,pred,s=10,alpha=.25)
        lim=max(abs(truth))*1.05;ax.plot([-lim,lim],[-lim,lim],'k--',lw=1)
        ax.set_title(labels[n].replace('\n',' '));ax.set_xlabel('True hidden-state difference (mm)');ax.set_ylabel('Predicted difference (mm)')
    ns=['history_state','history_state_swapped'];vals=[summary[f'{n}/test_wait']['paired_effect_NRMSE'] for n in ns]
    mu=np.array([v['mean'] for v in vals]);axs[2].bar(range(2),mu,color=[colors[n] for n in ns],
       yerr=[mu-np.array([v['ci_low'] for v in vals]),np.array([v['ci_high'] for v in vals])-mu],capsize=3)
    axs[2].axhline(1,color='k',ls='--');axs[2].set_xticks(range(2),[labels[n] for n in ns]);axs[2].set_ylabel('Paired effect NRMSE')
    fig.tight_layout();fig.savefig(fd/'03_state_recovery_and_exchange.png',dpi=180);plt.close(fig)

    fig,axs=plt.subplots(2,2,figsize=(11,7))
    for ax,n in zip(axs.ravel(),MODEL_NAMES):
        for seed in cfg['seeds']:
            logs=json.loads((out/'logs'/f'{n}_{seed}.json').read_text())
            ax.plot([r['step'] for r in logs],[r['val_loss'] for r in logs],label=f'seed {seed}')
        ax.set_title(labels[n].replace('\n',' '));ax.set_yscale('log');ax.set_xlabel('Optimizer updates');ax.set_ylabel('Validation loss');ax.legend(frameon=False,fontsize=8)
    fig.tight_layout();fig.savefig(fd/'04_convergence.png',dpi=180);plt.close(fig)

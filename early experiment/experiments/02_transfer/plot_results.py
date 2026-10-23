"""Publication figures from executed simulation only; no invented responses."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

OUT=ROOT/'runs'/'transfer_v1';FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
CFG=json.loads((ROOT/'config.json').read_text());RNG=np.random.default_rng(261019)
COLORS={'history_state':'#197E89','snapshot_state':'#C98652','history_single':'#87AAB4','gru_contact':'#9376B4',
        'classical_integral':'#3F4852','local_observer':'#73945B','oracle':'#20262B','reactive':'#A3A3A3',
        'state_swap':'#B9535F','state_average':'#DAAE6D'}
LABELS={'history_state':'History state','snapshot_state':'Current state','history_single':'History, one control',
        'gru_contact':'Conditioned GRU','classical_integral':'Classical integral','local_observer':'Local observer',
        'oracle':'Oracle','reactive':'Reactive','state_swap':'Swapped state','state_average':'Pair-mean state'}
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':7,
   'axes.titlesize':8,'axes.labelsize':7,'legend.fontsize':6,'axes.spines.top':False,'axes.spines.right':False,
   'axes.linewidth':.7,'lines.linewidth':1.3,'svg.fonttype':'none','pdf.fonttype':42,'savefig.facecolor':'white'})


def all_runs(name):
    seeds=CFG['seeds'] if name in ['history_state','snapshot_state','history_single','gru_contact','state_swap','state_average'] else [0]
    return [dict(np.load(OUT/'metrics'/f'{name}_{s}.npz')) for s in seeds]


def mean_metric(name,key):return np.mean([m[key] for m in all_runs(name)],0)


def save(fig,name):
    fig.savefig(FIG/f'{name}.png',dpi=300)
    fig.savefig(FIG/f'{name}.svg')
    fig.savefig(FIG/f'{name}.pdf')
    plt.close(fig)


def panel(ax,letter,title):
    ax.set_title(f'{letter}   {title}',loc='left',pad=8)
    ax.grid(axis='y',alpha=.15,lw=.5)


def ci(values):
    boot=values[RNG.integers(0,len(values),(1000,len(values)))].mean(1)
    return np.quantile(boot,[.025,.975],axis=0)


def transfer():
    names=['classical_integral','local_observer','snapshot_state','history_state','history_single','gru_contact']
    fig,axs=plt.subplots(2,2,figsize=(7.2047,5.4),layout='constrained')
    x=np.arange(7);labels=[f'{int(k)}\n{int(d)}' for k,d in CFG['controllers_test']]
    for key,ax,unit,letter,title in [('force_mse',axs[0,0],'Force RMSE (N)','a','Transfer across future controllers'),
                                    ('position_mse',axs[0,1],'Position RMSE (mm)','b','Future motion is also predicted')]:
        for name in names:
            arr=mean_metric(name,key);values=np.sqrt(arr.mean((0,1,3,4)))
            if key=='position_mse':values*=1000
            if not np.all(np.isfinite(values)&(values>0)):
                raise ValueError('Log RMSE requires strictly positive finite errors; use a linear scale for exact-zero models.')
            ax.plot(x,values,'o-',markersize=3,label=LABELS[name],color=COLORS[name])
        ax.axvspan(3.5,6.5,color='#E5EBEF',alpha=.5,zorder=-2);ax.set_yscale('log');ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_xticks(x,labels);ax.set_xlabel('Future stiffness K (N/m) / damping D (N s/m)')
        ax.set_ylabel(unit);panel(ax,letter,title)
    axs[0,0].legend(ncol=2,loc='lower left')
    ax=axs[1,0]
    for i,name in enumerate(names):
        runs=all_runs(name);v=[np.sqrt(m['contrast_mse'][:,4:].sum()/m['contrast_signal'][:,4:].sum()) for m in runs]
        ax.bar(i,np.mean(v),color=COLORS[name],width=.6);ax.plot(np.full(len(v),i),v,'k.',ms=3)
    ax.axhline(1,color='.4',ls=':',lw=.8);ax.set_xticks(range(len(names)),[LABELS[n] for n in names],rotation=35,ha='right')
    ax.set_ylabel('Response-contrast NRMSE');panel(ax,'c','Same present, different future response')
    ax=axs[1,1];d=dict(np.load(OUT/'data'/'test_histories.npz'));true=d['z'][:,1,0]-d['z'][:,0,0]
    for name in ['snapshot_state','local_observer','history_state']:
        z=all_runs(name)[0]['grounded_state'];est=z[:,1,0]-z[:,0,0]
        ax.scatter(true*1000,est*1000,s=8,alpha=.55,color=COLORS[name],label=LABELS[name],rasterized=True)
    lim=max(np.max(np.abs(true))*1000,1e-3)*1.1;ax.plot([-lim,lim],[-lim,lim],color='.3',ls=':',lw=.8)
    ax.set_xlabel('True fast-mode state contrast (mm)');ax.set_ylabel('Estimated contrast (mm)');ax.legend(loc='upper left')
    panel(ax,'d','Which hidden state was retained?')
    save(fig,'01_transfer')


def heatmaps():
    snap=mean_metric('snapshot_state','force_mse');hist=mean_metric('history_state','force_mse')
    error=np.sqrt(snap.mean((0,1,4)))-np.sqrt(hist.mean((0,1,4)))
    gain=(mean_metric('snapshot_state','decision_cost')-mean_metric('history_state','decision_cost')).mean((0,1,4))
    fig,axs=plt.subplots(1,2,figsize=(7.2047,3.4),layout='constrained')
    for ax,a,title,letter,unit in [(axs[0],error,'Prediction value of history','a','RMSE reduction (N)'),
                                 (axs[1],gain,'Action value of history','b','Cost reduction (s)')]:
        lim=max(np.max(np.abs(a)),1e-6);im=ax.imshow(a,cmap='RdBu_r',vmin=-lim,vmax=lim,aspect='auto')
        ax.set_xticks(range(3),[str(v) for v in CFG['test_waits']]);ax.set_xlabel('Base waiting time (s)')
        ax.set_yticks(range(7),[f'K={k}, D={d}'+(' *' if j>=4 else '') for j,(k,d) in enumerate(CFG['controllers_test'])])
        for r in range(7):
            for c in range(3):ax.text(c,r,f'{a[r,c]:.3f}',ha='center',va='center',fontsize=7,color='white' if abs(a[r,c])>.65*lim else '#222222')
        ax.set_title(f'{letter}   {title}',loc='left');fig.colorbar(im,ax=ax,label=unit,shrink=.8)
    save(fig,'02_control_wait')


def tradeoff():
    names=['oracle','classical_integral','local_observer','snapshot_state','history_state','gru_contact','reactive']
    fig,axs=plt.subplots(2,2,figsize=(7.2047,5.5),layout='constrained');caps=np.array(CFG['force_limits'])
    for ax,key,letter,title,ylabel in [(axs[0,0],'decision_cost','a','Speed with failure costs included','Penalized completion time (s)'),
        (axs[0,1],'decision_success','b','Safe task completion','Success (%)'),
        (axs[1,0],'decision_unsafe','c','True force-limit violations','Violation (%)')]:
        for name in names:
            a=mean_metric(name,key)[:,:,4:].mean((1,2,3));avg=a.mean(0);lo,hi=ci(a)
            scale=100 if key!='decision_cost' else 1
            ax.plot(caps,avg*scale,color=COLORS[name],label=LABELS[name],ls='--' if name in ['oracle','reactive'] else '-')
            if name in ['snapshot_state','history_state']:ax.fill_between(caps,lo*scale,hi*scale,color=COLORS[name],alpha=.13,lw=0)
        panel(ax,letter,title);ax.set_xlabel('Force limit (N)');ax.set_ylabel(ylabel)
    axs[0,0].legend(ncol=2,fontsize=6)
    ax=axs[1,1];methods=['oracle','snapshot_state','history_state','gru_contact'];colors=['#3E728B','#80A5B6','#B9CFD8','#D8BD87','#8BA892','#E7E7E7']
    labels=['Fast','Slow','Gentle','Wait + fast','Shallow','Reject']
    for i,name in enumerate(methods):
        ch=np.concatenate([r['decision_choice'][:,:,4:].ravel() for r in all_runs(name)]);left=0.
        for j,code in enumerate([0,1,2,3,4,-1]):
            frac=np.mean(ch==code)*100;ax.barh(i,frac,left=left,color=colors[j],height=.6,label=labels[j] if i==0 else None);left+=frac
    ax.set_yticks(range(4),[LABELS[n] for n in methods]);ax.set_xlabel('Decisions across fixed cap sweep (%)');ax.set_xlim(0,100)
    ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.19));panel(ax,'d','What does the selector actually choose?')
    save(fig,'03_action_tradeoff')


def mechanisms():
    names=['snapshot_state','history_state','history_single','gru_contact','state_average','state_swap']
    fig,axs=plt.subplots(1,3,figsize=(7.2047,3.2),layout='constrained')
    for ax,key,letter,title,ylabel in [(axs[0],'contrast_mse','a','State interventions','Response-contrast NRMSE'),
              (axs[1],'decision_cost','b','Effect on selected actions','Penalized time (s)')]:
        for j,name in enumerate(names):
            vals=[]
            for r in all_runs(name):
                val=np.sqrt(r[key][:,4:].sum()/r['contrast_signal'][:,4:].sum()) if key=='contrast_mse' else r[key][:,:,4:].mean()
                vals.append(val)
            ax.bar(j,np.mean(vals),color=COLORS[name]);ax.plot(np.full(len(vals),j),vals,'k.',ms=3)
        ax.set_xticks(range(len(names)),[LABELS[n] for n in names],rotation=60,ha='right');ax.set_ylabel(ylabel);panel(ax,letter,title)
    truth=dict(np.load(OUT/'metrics'/'truth.npz'));peaks=truth['peak'][:,:,4:]
    # Nearest candidate peak to the common selector boundary, never a data inclusion rule.
    distance=np.min(np.abs(peaks[...,None]-(np.array(CFG['force_limits'])-CFG['planning_force_margin'])),axis=-2)
    benefit=(mean_metric('snapshot_state','decision_cost')-mean_metric('history_state','decision_cost'))[:,:,4:]
    bins=[0,.03,.1,.3,1.,np.inf];vals=[];counts=[]
    for a,b in zip(bins[:-1],bins[1:]):
        mask=(distance>=a)&(distance<b);vals.append(float(benefit[mask].mean()) if mask.any() else 0.);counts.append(int(mask.sum()))
    ax=axs[2];ax.bar(range(5),vals,color=COLORS['history_state']);ax.axhline(0,color='.4',lw=.7)
    ax.set_xticks(range(5),['<.03','.03–.1','.1–.3','.3–1','≥1'],rotation=35)
    ax.set_xlabel('Distance to candidate force boundary (N)');ax.set_ylabel('History cost reduction (s)');panel(ax,'c','Where can accuracy change a decision?')
    for i,v in enumerate(vals):ax.annotate(f'n={counts[i]}',(i,v),xytext=(0,4 if v>=0 else -9),textcoords='offset points',ha='center',fontsize=5.5)
    save(fig,'06_mechanism')
    (FIG/'boundary_bins.json').write_text(json.dumps({'bins':[0,.03,.1,.3,1,'infinity'],'count':counts,'benefit_s':vals},indent=2),encoding='utf-8')


def export_table():
    rows=[]
    for name in ['oracle','classical_integral','local_observer',*['snapshot_state','history_state','history_single','gru_contact'],'state_swap','state_average','reactive']:
        rr=all_runs(name);cost=np.stack([r['decision_cost'] for r in rr]);paircost=cost.mean(0)[:,:,4:].mean((1,2,3,4));lo,hi=ci(paircost[:,None])[:,0]
        row={'method':name,'cost_s':float(paircost.mean()),'cost_ci_low':float(lo),'cost_ci_high':float(hi),
          'success':float(np.mean([r['decision_success'][:,:,4:].mean() for r in rr])),
          'unsafe':float(np.mean([r['decision_unsafe'][:,:,4:].mean() for r in rr]))}
        if 'force_mse' in rr[0]:
            row.update(force_rmse_N=float(np.sqrt(np.mean([r['force_mse'][:,:,4:].mean() for r in rr]))),
                position_rmse_mm=float(1000*np.sqrt(np.mean([r['position_mse'][:,:,4:].mean() for r in rr]))),
                contrast_nrmse=float(np.sqrt(np.sum([r['contrast_mse'][:,4:].sum() for r in rr])/np.sum([r['contrast_signal'][:,4:].sum() for r in rr]))),
                reject=float(np.mean([r['decision_reject'][:,:,4:].mean() for r in rr])))
        rows.append(row)
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (FIG/'main_results.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    (FIG/'main_results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    # Seed-averaged, paired whole-history bootstrap for main decision contrast.
    diff=(mean_metric('snapshot_state','decision_cost')-mean_metric('history_state','decision_cost'))[:,:,4:].mean((1,2,3,4))
    lo,hi=ci(diff[:,None])[:,0]
    (FIG/'paired_comparison.json').write_text(json.dumps({'history_cost_gain_s':float(diff.mean()),'ci95':[float(lo),float(hi)],
        'unit':'128 complete history pairs; all controller, wait, action-cap branches grouped; training seeds averaged'},indent=2),encoding='utf-8')


if __name__=='__main__':
    transfer();heatmaps();tradeoff();mechanisms();export_table()

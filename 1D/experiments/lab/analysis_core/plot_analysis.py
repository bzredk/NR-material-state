"""Paper-size diagnostics from validated CSV and held-out predictions.

All data are retained in episode summaries; descriptive trace selection is
deterministic and recorded in captions. Synthetic provenance is displayed.
"""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import argparse,csv,itertools
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
from pilot_io import load_dataset,read_json,local_output,write_csv,write_json,contact_position

plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
 'font.size':7,'axes.titlesize':8,'axes.labelsize':7,'xtick.labelsize':6.5,'ytick.labelsize':6.5,
 'legend.fontsize':6,'legend.frameon':False,'axes.spines.top':False,'axes.spines.right':False,
 'axes.linewidth':.65,'lines.linewidth':1.,'svg.fonttype':'none','pdf.fonttype':42})
COLORS={'L2':'#747C85','L4':'#383F49','S2':'#C4A459','S4':'#C27635','Q2':'#93A797','Q4':'#477666','R2':'#237EB0','SR2':'#82659B'}
STYLE={'L2':':','L4':'--','S2':':','S4':'-.','Q2':':','Q4':'--','R2':'-','SR2':'--'}
COLORS.update(L6='#252B31',S6='#9E562A',Q6='#245846')
STYLE.update(L6=':',S6=':',Q6=':')
CONDITION=['#237EB0','#C27635','#68958B','#82659B']
PHASE_COLORS=['#EDF0F2','#E4EDF5','#EEE5D6','#EAE4F1','#E4EFEA','#E5EAF3','#EEE5D6','#EDF0F2']

def csvrows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def finish(fig,out,name,title,label):
    fig.suptitle(title,x=.07,ha='left',fontsize=10,fontweight='bold')
    fig.text(.07,.012,label,fontsize=6,color='#51565C')
    for i,ax in enumerate(fig.axes):
        ax.text(-.12,1.08,chr(97+i),transform=ax.transAxes,fontweight='bold',fontsize=9)
        ax.grid(axis='y',color='#DFE2E5',linewidth=.4,zorder=0)
    fig.tight_layout(rect=(0,.045,1,.94),h_pad=1.9,w_pad=1.4)
    fig.savefig(out/f'{name}.png',dpi=300)
    fig.savefig(out/f'{name}.svg')
    fig.savefig(out/f'{name}.pdf')
    plt.close(fig)

def pred(preds,axis,model,ep,mode):return preds[f'{axis}__{model}__{ep["episode_id"]}__{mode}']

def phases(ax,e):
    labels=list(dict.fromkeys(e['phase']))
    for j,label in enumerate(labels):
        idx=np.flatnonzero(e['phase']==label)
        a,b=e['t'][idx[0]],e['t'][idx[-1]]
        ax.axvspan(a,b,color=PHASE_COLORS[j%len(PHASE_COLORS)],zorder=-1)
        ax.text((a+b)/2,1.015,label,transform=ax.get_xaxis_transform(),ha='center',fontsize=5.5,rotation=0)

def main(dataset,results,output):
    out=local_output(output);episodes,meta,checks=load_dataset(dataset)
    preds=np.load(Path(results)/'predictions.npz');metrics=csvrows(Path(results)/'metrics.csv')
    mode='command' if any(r['mode']=='command' for r in metrics) else 'constitutive'
    source=('SYNTHETIC SOFTWARE CONTROL — not real foam data' if meta['data_type']=='synthetic_validation' else 'REAL MEASUREMENTS')
    footer=source+' | lines/dots: individual repeats; no population confidence intervals'
    amplitudes=sorted({e['amplitude'] for e in episodes});waits=sorted({e['wait'] for e in episodes})
    programs=sorted({e['program'] for e in episodes});mid=waits[len(waits)//2]
    selected=[e for e in episodes if e['amplitude']==amplitudes[-1] and e['wait']==mid and e['program']=='overshoot']
    if not selected:selected=[e for e in episodes if e['amplitude']==amplitudes[-1] and e['wait']==mid and e['program']==programs[-1]]
    e=selected[0];labels=[]

    fig,axs=plt.subplots(3,1,figsize=(7.2047,155/25.4))
    for j,ee in enumerate(selected):
        axs[0].plot(ee['t'],ee['x']*1000,color='#4C5964',alpha=.65,label='Actual position (two repeats)' if j==0 else None)
        axs[1].plot(ee['t'],ee['f'],color='#4C5964',alpha=.55,label='Measured force' if j==0 else None)
    axs[0].plot(e['t'],e['u']*1000,'--',color='#237EB0',label='Command');phases(axs[0],e)
    for model in ['L4','S4','R2']:
        pp=pred(preds,'wait',model,e,mode);axs[1].plot(e['t'],pp[:,0],STYLE[model],color=COLORS[model],label=model)
        mask=(e['phase']=='recontact')|(e['phase']=='rehold')
        tr=e['t'][mask]-e['t'][np.flatnonzero(mask)[0]]
        axs[2].plot(tr,pp[mask,0],STYLE[model],color=COLORS[model],label=model)
    for ee in selected:
        mask=(ee['phase']=='recontact')|(ee['phase']=='rehold');tt=ee['t'][mask];tt=tt-tt[0]
        axs[2].plot(tt,ee['f'][mask],color='#1D2024',alpha=.4,lw=.7)
    axs[0].set(ylabel='Position (mm)');axs[0].legend(loc='upper right',ncol=2)
    axs[1].set(xlabel='Time from episode start (s)',ylabel='Force (N)');axs[1].legend(ncol=4,loc='upper left')
    axs[1].axvline(e['t'][e['forecast']],color='#222222',lw=.6,ls=':')
    axs[2].set(xlabel='Time from recontact command (s)',ylabel='Force (N)',title=f'Held-out wait: {mid:g} s | {mode} prediction begins at retract onset')
    finish(fig,out,'01_interaction','From preload to the next contact',footer)

    fig,axs=plt.subplots(2,2,figsize=(7.2047,140/25.4))
    for pi,program in enumerate(programs):
        for ai,amp in enumerate(amplitudes):
            group=[ee for ee in episodes if ee['amplitude']==amp and ee['program']==program]
            color=CONDITION[ai+2*pi]
            for j,ee in enumerate(group):
                mask=np.isin(ee['phase'],['preload','hold','retract'])
                axs[0,pi].plot(ee['x'][mask]*1000,ee['f'][mask],color=color,alpha=.45,lw=.65,
                    label=f'{amp*1000:g} mm command; n={len(group)}' if j==0 else None)
                h=ee['phase']=='hold';th=ee['t'][h]-ee['t'][h][0];force=ee['f'][h]
                text=f'{program}, {amp*1000:g} mm'
                axs[1,0].plot(th,force,color=color,alpha=.45,lw=.65,label=text if j==0 else None)
                if abs(force[0])>meta['analysis']['contact_threshold_N']:
                    axs[1,1].plot(th,force/force[0],color=color,alpha=.45,lw=.65)
            axs[0,pi].set(title=program,xlabel='Actual compression-axis position (mm)',ylabel='Force (N)');axs[0,pi].legend()
    axs[1,0].set(xlabel='Time in hold (s)',ylabel='Force (N)',title='Raw force: every preloading repeat');axs[1,0].legend(ncol=2)
    axs[1,1].set(xlabel='Time in hold (s)',ylabel='Force / first hold force',title='Shape comparison; actual motion is not clamped')
    finish(fig,out,'02_force_relaxation','Separate response scale from response shape',footer)

    observables=[]
    for ee in episodes:
        m=(ee['phase']=='recontact')|(ee['phase']=='rehold')
        cp=contact_position(ee['t'],ee['x'],ee['f'],ee['phase'],meta['analysis']['contact_threshold_N'],meta['analysis']['contact_persistence_s'])
        observables.append(dict(episode_id=ee['episode_id'],program=ee['program'],amplitude_m=ee['amplitude'],wait_s=ee['wait'],repeat=ee['repeat'],
             contact_position_mm=None if cp is None else cp*1000,peak_N=float(max(ee['f'][m])),impulse_Ns=float(np.trapezoid(ee['f'][m],ee['t'][m]))))
    write_csv(out/'wait_observables.csv',observables)
    fig,axs=plt.subplots(1,3,figsize=(7.2047,83/25.4))
    for ci,(program,amp) in enumerate(itertools.product(programs,amplitudes)):
        group=[r for r in observables if r['program']==program and r['amplitude_m']==amp]
        for ax,key,yl in zip(axs,['contact_position_mm','peak_N','impulse_Ns'],['Threshold contact position (mm)','Peak force (N)','Recontact + hold impulse (N s)']):
            for repeat,marker in [('1','o'),('2','s')]:
                rr=sorted([r for r in group if r['repeat']==repeat],key=lambda r:r['wait_s'])
                yy=[r[key] if r[key] is not None else np.nan for r in rr]
                ax.plot([r['wait_s'] for r in rr],yy,marker=marker,color=CONDITION[ci],markersize=3,
                  alpha=.75,lw=.7,label=f'{program}, {amp*1000:g} mm' if repeat=='1' else None)
            ax.set(xscale='log' if np.all(np.asarray(waits)>0) else 'linear',xlabel='Wait (s)',ylabel=yl);ax.set_xticks(waits,labels=[f'{w:g}' for w in waits]);ax.xaxis.set_minor_locator(NullLocator())
    axs[1].legend(loc='upper center',bbox_to_anchor=(.5,-.24),ncol=2)
    finish(fig,out,'03_wait_effect','Recovery matters through the next action',footer+'\nContact uses a fixed noise-based force threshold; it is not a free-surface measurement.')

    synthetic=meta['data_type']=='synthetic_validation'
    fig,axs=plt.subplots(3 if synthetic else 2,3,figsize=(7.2047,(175 if synthetic else 130)/25.4))
    modelnames=[name for name in COLORS if any(r['model']==name for r in metrics)]
    plot_trace_ids={}
    for j,axis in enumerate(['amplitude','wait','program']):
        rows=[r for r in metrics if r['axis']==axis and r['mode']==mode]
        testids={r['episode_id'] for r in rows}
        candidates=[ee for ee in episodes if ee['episode_id'] in testids]
        # Predeclared lexicographic representative, no error-dependent selection.
        target=sorted(candidates,key=lambda ee:(-ee['amplitude'],abs(ee['wait']-mid),ee['program'],ee['repeat']))[0]
        plot_trace_ids[axis]=target['episode_id']
        mask=np.isin(target['phase'],['recontact','rehold']);tr=target['t'][mask]-target['t'][mask][0]
        for ee in candidates:
            if (ee['amplitude'],ee['wait'],ee['program'])==(target['amplitude'],target['wait'],target['program']):
                mm=np.isin(ee['phase'],['recontact','rehold']);tt=ee['t'][mm]-ee['t'][mm][0]
                axs[0,j].plot(tt,ee['f'][mm],color='#15171A',alpha=.45,lw=.8,label='Observed' if ee['repeat']=='1' else None)
        for name in modelnames:
            pp=pred(preds,axis,name,target,mode)
            axs[0,j].plot(tr,pp[mask,0],STYLE[name],color=COLORS[name],label=name)
        axs[0,j].set(title=f'Held-out {axis}',xlabel='Recontact time (s)',ylabel='Force (N)')
        for mi,name in enumerate(modelnames):
            vals=[float(r['force_rmse_N']) for r in rows if r['model']==name]
            offset=np.linspace(-.18,.18,len(vals));axs[1,j].scatter(mi+offset,vals,s=10,color=COLORS[name],alpha=.7)
            axs[1,j].plot([mi-.25,mi+.25],[np.median(vals)]*2,color='#222222',lw=1.3)
        axs[1,j].set_xticks(range(len(modelnames)),modelnames,rotation=45)
        positive=np.all(np.array([float(r['force_rmse_N']) for r in rows])>0)
        axs[1,j].set(yscale='log' if positive else 'linear',ylabel='Per-episode force RMSE (N)',title='All test episodes; median')
    axs[0,1].legend(ncol=9,loc='upper center',bbox_to_anchor=(.5,1.35),handlelength=1.2,columnspacing=.6)
    controls_present=synthetic
    for j,kind in enumerate(['linear','static','rate'] if synthetic else []):
        summaryfile=ROOT/'runs'/f'final_{kind}'/'summary.csv'
        if not summaryfile.exists():
            axs[2,j].text(.5,.5,'Software control not available',ha='center',transform=axs[2,j].transAxes);controls_present=False;continue
        rr=csvrows(summaryfile)
        for mi,name in enumerate(modelnames):
            vals=[float(r['mean_force_rmse_N']) for r in rr if r['model']==name and r['mode']==mode]
            axs[2,j].scatter(np.repeat(mi,len(vals)),vals,s=16,color=COLORS[name])
        axs[2,j].set_xticks(range(len(modelnames)),modelnames,rotation=45)
        positive=np.all(np.array([float(r['mean_force_rmse_N']) for r in rr])>0)
        axs[2,j].set(yscale='log' if positive else 'linear',ylabel='Split-mean RMSE (N)',title=f'Software control: {kind}')
    detail=f'Top/middle: {mode}; bottom: synthetic controls, three split means per model (not independent replications).' if synthetic else f'{mode} predictions and all held-out real episodes.'
    finish(fig,out,'04_cross_condition','Predict withheld conditions, then challenge the explanation',footer+'\n'+detail)

    fig,axs=plt.subplots(2,3,figsize=(7.2047,145/25.4));axis='wait'
    test=[ee for ee in episodes if ee['wait']==mid]
    residue_sources=[]
    for j,name in enumerate(['L4','S4','R2']):
        allx=[];ally=[]
        for ee in test:
            pp=pred(preds,axis,name,ee,mode);mask=np.isin(ee['phase'],['recontact','rehold'])
            tr=ee['t'][mask]-ee['t'][mask][0];err=pp[mask,0]-ee['f'][mask]
            axs[0,j].plot(tr,err,color=CONDITION[(ee['program']=='slow')*2+(ee['amplitude']==amplitudes[-1])],alpha=.55,lw=.65,
                         label=f'{ee["program"]}, {ee["amplitude"]*1000:g} mm' if ee['repeat']=='1' else None)
            allx.extend(ee['x'][mask]*1000);ally.extend(err)
            for tx,xx,er in zip(tr,ee['x'][mask],err):
                residue_sources.append(dict(model=name,episode_id=ee['episode_id'],time_from_recontact_s=float(tx),
                    compression_position_m=float(xx),residual_N=float(er),program=ee['program'],amplitude_m=ee['amplitude'],wait_s=ee['wait']))
        axs[0,j].axhline(0,color='#222222',lw=.6);axs[0,j].set(title=name,xlabel='Recontact time (s)',ylabel='Prediction - measured (N)')
        allx=np.array(allx);ally=np.array(ally);edges=np.linspace(allx.min(),allx.max(),13)
        centers=[];med=[];lo=[];hi=[]
        for left,right in zip(edges[:-1],edges[1:]):
            vals=ally[(allx>=left)&(allx<=right if right==edges[-1] else allx<right)]
            if len(vals):centers.append((left+right)/2);med.append(np.median(vals));lo.append(np.quantile(vals,.1));hi.append(np.quantile(vals,.9))
        axs[1,j].fill_between(centers,lo,hi,color=COLORS[name],alpha=.2)
        axs[1,j].plot(centers,med,color=COLORS[name]);axs[1,j].axhline(0,color='#222222',lw=.6)
        axs[1,j].set(xlabel='Actual position (mm)',ylabel='Residual (N)',title='Compression dependence')
    axs[0,1].legend(ncol=4,loc='upper center',bbox_to_anchor=(.5,1.32),handlelength=1.2,columnspacing=.7)
    limit=max(abs(ax.get_ylim()[0]) for ax in axs[0])+0.03
    limit=max(limit,max(abs(ax.get_ylim()[1]) for ax in axs[0]))
    for ax in axs.flat:ax.set_ylim(-limit,limit)
    finish(fig,out,'05_residuals','A mechanism should remove structured prediction errors',footer+'\nColors encode amplitude/history; pooled bands are descriptive, not confidence intervals.')
    write_csv(out/'residual_source_data.csv',residue_sources)

    previous=ROOT.parent/'material-state-round2-2026-10-19/runs/round2_v1/summary.json'
    if previous.exists():
        summary=read_json(previous);names=['classical_integral','local_observer','snapshot_state','history_state','gru_contact','gru_force']
        aliases=['Classical integral','Local observer','Current observation','History state','GRU + contact','GRU force']
        fig,axs=plt.subplots(1,2,figsize=(7.2047,83/25.4));source_rows=[]
        for ax,metric,title in zip(axs,['paired_effect_NRMSE','force_rmse_N'],['Difference-response error (NRMSE)','Absolute force error (N)']):
            for j,name in enumerate(names):
                s=summary[name+'/test_wait'][metric];color='#237EB0' if name=='history_state' else '#697580'
                ax.errorbar(s['mean'],j,xerr=[[s['mean']-s['ci_low']],[s['ci_high']-s['mean']]],fmt='o',color=color,markersize=4,capsize=2)
                source_rows.append(dict(model=name,metric=metric,**{k:s[k] for k in ['mean','ci_low','ci_high']}))
            ax.set_yticks(range(len(names)),aliases);ax.invert_yaxis();ax.set_xscale('log');ax.set_xlabel(title)
        finish(fig,out,'00_round2_bridge','Known linear physics: memory helps, a learned law is not yet needed',
          'EXISTING ROUND-2 SIMULATION | 192 history pairs; original 95% pair/seed bootstrap intervals; no retraining')
        write_csv(out/'round2_source_data.csv',source_rows)
    write_json(out/'qa_notes.json',dict(data_type=meta['data_type'],dataset=str(Path(dataset).resolve()),
       episodes=len(episodes),raw_samples=sum(len(e['t']) for e in episodes),rows_removed=0,
       representative_traces=plot_trace_ids,interaction_episodes=[e['episode_id'] for e in selected],
       normalized_hold='divide by first hold force only when above declared contact threshold; not equilibrium-normalized relaxation',
       residual_bands='12 uniform displacement bins; sample quantiles 10/90, not uncertainty of mean',
       controls_present=controls_present,format='PNG 300 dpi + editable SVG + TrueType PDF',
       notes='No real recordings available at initial creation. Previous figures left unchanged.'))
    print(f'Figures written to {out}')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('dataset');p.add_argument('--results',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    main(a.dataset,a.results,a.output)

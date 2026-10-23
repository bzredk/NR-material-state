"""Regenerate synchronized traces using explicit, recorded case-selection rules."""
import json
import numpy as np
from plot_results import ROOT,OUT,FIG,CFG,plt,COLORS,LABELS,save,panel
from dataset import load
from evaluate import build_context,predict


def metric(name):return dict(np.load(OUT/'metrics'/f'{name}_{11 if name in ["history_state","snapshot_state","gru_contact"] else 0}.npz'))


def subset(d,i):return {k:v[i:i+1] for k,v in d.items()}


def generate():
    d=dict(np.load(OUT/'data'/'test_histories.npz'));hm=metric('history_state');sm=metric('snapshot_state');om=metric('oracle')
    gain=sm['decision_cost']-hm['decision_cost'];mask=hm['decision_success']&(gain>.2)
    mask[:,:,:4]=False;indices=np.argwhere(mask)
    if len(indices):
        values=gain[mask];ix=indices[np.argsort(values)[len(values)//2]];rule='median positive cost gain >0.2s among held-out-controller decisions where history succeeds; seed 11'
    else:
        unseen_gain=gain[:,:,4:];ix=np.array(np.unravel_index(np.argmax(unseen_gain),unseen_gain.shape));ix[2]+=4
        rule='fallback maximum gain on held-out controllers, explicitly exploratory'
    n,member,c,w,l=map(int,ix);dd=subset(d,n);ctx=build_context(CFG,dd);shape=ctx['shape'];T=ctx['u'].shape[1]
    truth,_=predict(CFG,OUT,dd,ctx,'oracle',0);truth=truth.reshape(*shape,T,3)
    predictions={};states={}
    for name in ['history_state','snapshot_state','gru_contact','classical_integral']:
        p,z=predict(CFG,OUT,dd,ctx,name,11);predictions[name]=p.reshape(*shape,T,3)
        if z is not None:states[name]=z.tolist()
    u=ctx['u'].reshape(*shape,T);t=np.arange(1,T+1)*CFG['dt'];cap=CFG['force_limits'][l]
    fig,axs=plt.subplots(3,1,figsize=(7.2047,5.2),sharex=True,layout='constrained')
    choices={};sources={}
    for name in ['snapshot_state','history_state','gru_contact']:
        met=metric(name);a=int(met['decision_choice'][n,member,c,w,l]);choices[name]=a
        if a<0:continue
        actual=truth[0,member,c,w,a];pred=predictions[name][0,member,c,w,a]
        actual_time=met['decision_time'][n,member,c,w,l]
        end=T
        color=COLORS[name];label=LABELS[name]+' / '+CFG['actions'][a]['name']
        axs[0].plot(t[:end],u[0,member,c,w,a,:end]*1000,color=color,label=label)
        axs[1].plot(t[:end],actual[:end,0]*1000,color=color)
        axs[1].plot(t[:end],pred[:end,0]*1000,color=color,ls='--',lw=.9)
        axs[2].plot(t[:end],actual[:end,2],color=color)
        axs[2].plot(t[:end],pred[:end,2],color=color,ls='--',lw=.9)
        if np.isfinite(actual_time):axs[1].axvline(actual_time,color=color,ls=':',lw=.6,alpha=.7)
        sources[name]=dict(command=u[0,member,c,w,a].tolist(),truth=actual.tolist(),prediction=pred.tolist(),first_goal_time_s=float(actual_time) if np.isfinite(actual_time) else None,samples_displayed=end)
    axs[0].legend(loc='upper right',ncol=1);axs[1].axhline(CFG['goal_position']*1000,color='.4',ls=':',lw=.8)
    axs[2].axhline(cap,color='#A63D4E',ls=':',lw=1,label=f'Force limit {cap:.2f} N');axs[2].legend(loc='upper right')
    zoom=axs[2].inset_axes([.57,.42,.26,.48]);peak_t=None
    for name,source in sources.items():
        actual=np.asarray(source['truth']);pred=np.asarray(source['prediction'])
        if name=='snapshot_state':peak_t=t[np.argmax(actual[:,2])]
        zoom.plot(t,actual[:,2],color=COLORS[name],lw=1)
        zoom.plot(t,pred[:,2],color=COLORS[name],ls='--',lw=.7)
    if peak_t is None:peak_t=t[np.argmax(np.asarray(sources['history_state']['truth'])[:,2])]
    zoom.set_xlim(max(0,peak_t-.15),peak_t+.15);zoom.set_ylim(cap-.18,cap+.18)
    zoom.axhline(cap,color='#A63D4E',ls=':',lw=.7);zoom.tick_params(labelsize=5)
    zoom.set_title('Force-boundary detail',fontsize=5.5)
    for ax,letter,title,ylabel in zip(axs,['a','b','c'],['Selected command','Motion: solid actual, dashed prediction','Contact force: solid actual, dashed prediction'],['Command (mm)','Position (mm)','Force (N)']):
        ax.set_ylabel(ylabel);ax.axvspan(0,.3,color='.9',alpha=.5);panel(ax,letter,title)
    axs[-1].set_xlabel('Time from start of release (s); controller changes at 0.3 s')
    fig.suptitle(f'One decision: K={CFG["controllers_test"][c][0]}, D={CFG["controllers_test"][c][1]}, base wait={CFG["test_waits"][w]} s',fontsize=9)
    save(fig,'04_decision_case')
    # The exact same grounded state and future command fan out into three controllers.
    fig,axs=plt.subplots(3,3,figsize=(7.2047,5.2),sharex=True,sharey='row',layout='constrained')
    for col,control in enumerate([0,4,5]):
        a=0;wi=0;actual=truth[0,member,control,wi,a];hh=predictions['history_state'][0,member,control,wi,a]
        ss=predictions['snapshot_state'][0,member,control,wi,a]
        axs[0,col].plot(t,u[0,member,control,wi,a]*1000,color='.3')
        for row,channel,scale in [(1,0,1000),(2,2,1)]:
            axs[row,col].plot(t,actual[:,channel]*scale,color='#252B33',label='Actual')
            axs[row,col].plot(t,hh[:,channel]*scale,color=COLORS['history_state'],ls='--',label='History prediction')
            axs[row,col].plot(t,ss[:,channel]*scale,color=COLORS['snapshot_state'],ls=':',label='Current prediction')
        axs[0,col].set_title(f'K={CFG["controllers_test"][control][0]}, D={CFG["controllers_test"][control][1]}')
        axs[2,col].set_xlabel('Time (s)')
    for row,label in enumerate(['Command (mm)','Position (mm)','Force (N)']):axs[row,0].set_ylabel(label)
    axs[1,0].legend(fontsize=5.5);fig.suptitle('One fixed history-grounded state, three future controllers',fontsize=9)
    save(fig,'05_state_reuse')
    # Matched-present decision disagreement is diagnostic; retain all candidates count.
    oracle_disagree=(om['decision_choice'][:,0]!=om['decision_choice'][:,1])&(om['decision_choice'][:,0]>=0)&(om['decision_choice'][:,1]>=0)
    oracle_disagree[:,:4]=False
    info=dict(case_index=ix.tolist(),selection_rule=rule,eligible_decisions=len(indices),choices=choices,
       cap_N=cap,controller=CFG['controllers_test'][c],base_wait_s=CFG['test_waits'][w],states=states,
       same_present_oracle_different_actions=int(oracle_disagree.sum()),total_heldout_pair_decisions=int(np.prod(oracle_disagree[:,4:].shape)),
       source='fresh synthetic Maxwell test; predictions seed 11; no real data',trace=sources)
    (FIG/'case_source.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    # Export complete case arrays as reproducible numeric source data.
    np.savez_compressed(FIG/'case_source.npz',time=t,command=u,truth=truth,**predictions)


if __name__=='__main__':generate()


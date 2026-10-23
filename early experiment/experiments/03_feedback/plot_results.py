"""Paper-oriented plots from frozen logs; every displayed case was preselected."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from bridge import ROOT,C,load,methods,FITTED,TRUTH,advance,material_observed

S=json.loads((ROOT/"results/summary.json").read_text())
P=load("raw/prepared.npz")
D=load("raw/diagnostic_inputs.npz")
COL={"history":"#2467B2","snapshot":"#D57631","classical":"#3B8C69",
     "reactive":"#8C65B4","reactive30":"#7D7D7D"}
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.titlesize":11,
 "axes.labelsize":10,"figure.titlesize":14,"axes.spines.top":False,"axes.spines.right":False,
 "axes.grid":True,"grid.alpha":.16,"svg.fonttype":"none","pdf.fonttype":42,"savefig.dpi":240})
MANIFEST=[]
def export(fig,stem,question,reading):
    fig.savefig(ROOT/f"figures/{stem}.png",bbox_inches="tight")
    fig.savefig(ROOT/f"figures/{stem}.svg",bbox_inches="tight")
    fig.savefig(ROOT/f"figures/{stem}.pdf",bbox_inches="tight")
    plt.close(fig)
    MANIFEST.append(dict(figure=stem,question=question,interpretation=reading,
        source="existing frozen round3 checkpoints in the new round4 bridge simulation; no real data"))

def diag_family(prefix):
    if prefix=="classical":return load("raw/diagnostic_classical.npz")
    items=[load(f"raw/diagnostic_{prefix}_state_{s}.npz") for s in C["seeds"]]
    return {k:np.stack([x[k] for x in items]).mean(0) for k in items[0]}
def action_family(prefix):
    if prefix in ["classical","reactive_005","reactive_030"]:return load(f"raw/actions_{prefix}.npz")
    items=[load(f"raw/actions_{prefix}_state_{s}.npz") for s in C["seeds"]]
    return {k:(items[0][k] if k=="ids" else np.stack([x[k] for x in items]).mean(0)) for k in items[0]}
DH=diag_family("history");DS=diag_family("snapshot");DC=diag_family("classical")
AH=action_family("history");AS=action_family("snapshot");AC=action_family("classical")
AR=action_family("reactive_005");AR30=action_family("reactive_030")
FAMS=[("History",AH,COL["history"]),("Current",AS,COL["snapshot"]),("Classical",AC,COL["classical"]),
      ("Reactive .05",AR,COL["reactive"]),("Reactive .30",AR30,COL["reactive30"])]

def band(ax,arr,label,color,ls="-"):
    # arr: 1152 shared-command branches x time; cluster complete history pairs.
    pair=arr.reshape(C["pairs"],-1,arr.shape[-1]).mean(1)
    rng=np.random.default_rng(C["bootstrap_seed"])
    ix=rng.integers(C["pairs"],size=(C["bootstrap_samples"],C["pairs"]))
    mean=pair.mean(0);lo,hi=np.quantile(pair[ix].mean(1),[.025,.975],axis=0)
    ax.plot(D["offsets"]*.01,mean,label=label,color=color,ls=ls,lw=1.8)
    if ls=="-":ax.fill_between(D["offsets"]*.01,lo,hi,color=color,alpha=.12,lw=0)

def transfer():
    fig,ax=plt.subplots(2,2,figsize=(11.5,8.2),layout="constrained")
    for i,(lab,d,color) in enumerate([("History",DH,COL["history"]),("Current",DS,COL["snapshot"]),
                                     ("Classical",DC,COL["classical"])]):
        v=d["cut_force_rmse"].reshape(C["pairs"],-1).mean(1)
        xx=i+np.linspace(-.16,.16,len(v))
        ax[0,0].scatter(xx,v,s=13,alpha=.5,color=color)
        ax[0,0].plot([i-.2,i+.2],[v.mean()]*2,color=color,lw=3)
        ax[0,0].text(i,v.max()*1.13,f"{v.mean():.4f}",ha="center",color=color)
    ax[0,0].set_xticks(range(3),["History","Current","Classical"])
    ax[0,0].set(ylabel="Mean re-contact force RMSE (N)",yscale="log",
        title="A  Forecast from the original contact cut\nNo subsequent feedback; dots = history-pair means")
    raw_gain=(DS["cut_force_rmse"]-DH["cut_force_rmse"]).reshape(128,3,3).mean(0)*1000
    pre_gain=(DS["aligned"][:,8,0]-DH["aligned"][:,8,0]).reshape(128,3,3).mean(0)*1000
    for a,arr,title in [(ax[0,1],raw_gain,"B  Original-cut forecast advantage (mN)"),
                        (ax[1,0],pre_gain,"C  Advantage 20 ms before re-contact (mN)")]:
        lim=max(np.max(np.abs(arr)),.1)
        im=a.imshow(arr,cmap="RdBu",vmin=-lim,vmax=lim,aspect="auto")
        for r in range(3):
            for c in range(3):a.text(c,r,f"{arr[r,c]:.3f}" if lim<1 else f"{arr[r,c]:.1f}",
                ha="center",va="center",color="white" if abs(arr[r,c])>.55*lim else "#222")
        a.set_xticks(range(3),C["waits"]);a.set_yticks(range(3),["New K,D","Higher K","Higher D"])
        a.set(xlabel="Wait after release (s)",title=title);a.grid(False)
        fig.colorbar(im,ax=a,shrink=.8,label="Current minus history; positive favors history")
    for lab,d,col in [("History + feedback",DH,COL["history"]),("Current + feedback",DS,COL["snapshot"]),
                      ("Classical + feedback",DC,COL["classical"])]:
        band(ax[1,1],d["aligned"][:,:,0],lab,col)
    for lab,n,col in [("History, no force update","history_state_11_noinnovation",COL["history"]),
                       ("Current, no force update","snapshot_state_11_noinnovation",COL["snapshot"])]:
        band(ax[1,1],load(f"raw/diagnostic_{n}.npz")["aligned"][:,:,0],lab,col,"--")
    ax[1,1].axvline(0,color="black",lw=.8)
    ax[1,1].set(xlabel="Time from first re-contact (s)",ylabel="120-ms force forecast RMSE (N)",
        yscale="log",title="D  Common commands and measurements\nNo-update curves are diagnostics only")
    ax[1,1].legend(fontsize=8,loc="upper right")
    fig.suptitle("History transfers predictive information; available feedback removes most of the gap")
    export(fig,"01_prediction_transfer",
        "Does the frozen history state predict new-controller responses, and does its advantage survive new feedback?",
        "Original-cut forecasts favor history. Shared release and contact feedback makes online forecasts nearly coincide; classical integration remains a strong reference.")

def feedback():
    fig,ax=plt.subplots(2,2,figsize=(11.5,7.7),layout="constrained")
    for label,stem,color in [("History","history_state_11",COL["history"]),
                             ("Current","snapshot_state_11",COL["snapshot"]),("Classical","classical",COL["classical"])]:
        z=P["prefix_z_"+stem]
        err=np.sqrt(np.mean((z-P["prefix_truth"][:,:,2:])**2,axis=(0,2)))*1000
        ax[0,0].plot(np.arange(31)*.01,err,label=label,color=color,lw=1.8)
    ax[0,0].set(title="A  Correction already occurs during common release",
        xlabel="Time since original encoding cut (s)",ylabel="Two-state RMSE (mm)",yscale="log")
    ax[0,0].legend(fontsize=9)
    for label,d,col in [("History",DH,COL["history"]),("Current",DS,COL["snapshot"]),("Classical",DC,COL["classical"])]:
        band(ax[0,1],d["aligned"][:,:,2],label,col)
        band(ax[1,0],d["aligned"][:,:,4],label,col)
    ax[0,1].set(title="B  Action-relevant state projection",xlabel="Time from re-contact (s)",
                ylabel="Mean |kᵀ(state error)| (N)",yscale="log")
    ax[1,0].set(title="C  Online force correction",xlabel="Time from re-contact (s)",
                ylabel="Mean |kᵀ(state correction)| (N)")
    for a in [ax[0,1],ax[1,0]]:a.axvline(0,color="black",lw=.8)
    keys=["precontact","first_100ms","100_to_500ms","after_500ms"]
    vals=np.mean([[r[k+"_episode_fraction"] for k in keys] for r in S["action_differences"]],axis=0)*100
    ax[1,1].bar(range(4),vals,color=COL["history"],width=.6)
    for i,v in enumerate(vals):ax[1,1].text(i,v+.004,f"{v:.3f}%",ha="center")
    ax[1,1].set_xticks(range(4),["Before\ncontact","0–100 ms","100–500 ms",">500 ms"])
    ax[1,1].set(ylabel="Episodes with a changed rate (%)",ylim=(0,max(vals)*1.3+.01),
       title="D  History vs current: rare, transient action changes\n≥1 mm/s; while both tasks are still running")
    fig.suptitle("The bridge carries state and covariance; it also admits feedback before re-contact")
    export(fig,"02_feedback_and_action_change",
        "When do state estimates become similar, and do different estimates continue changing actions?",
        "The 0.3-s release brings the estimates together, while its common observer also perturbs initially accurate estimates. Rate differences occur in about 0.12% of branches and disappear after the first 100 ms in the matched ongoing-task comparison.")

def outcomes():
    fig,ax=plt.subplots(2,2,figsize=(11.5,8.1),layout="constrained")
    for i,(label,d,col) in enumerate(FAMS):
        vals=d["metrics"][:,0].reshape(C["pairs"],-1).mean(1)
        ax[0,0].scatter(i+np.linspace(-.13,.13,len(vals)),vals,s=12,color=col,alpha=.4)
        ax[0,0].plot([i-.2,i+.2],[vals.mean()]*2,color=col,lw=3)
        peak=d["metrics"][:,1].reshape(C["pairs"],-1).mean(1)
        ax[1,0].scatter(i+np.linspace(-.13,.13,len(peak)),peak,s=12,color=col,alpha=.4)
        ax[1,0].plot([i-.2,i+.2],[peak.mean()]*2,color=col,lw=3)
    labels=[x[0].replace(" ","\n") for x in FAMS]
    for a in [ax[0,0],ax[1,0]]:a.set_xticks(range(5),labels)
    ax[0,0].set(ylabel="Task completion time (s)",title="A  Actual completion time, including the wait\nAdd 0.3 s for the common release; all tasks complete")
    ax[1,0].set(ylabel="Mean peak force (N)",title="C  Peak over the full task and final release\nDots = pair means across controller/wait/cap")
    fail=np.array([100*np.mean(x[1]["metrics"][:,3]) for x in FAMS])
    ax[0,1].bar(range(5),fail,color=[x[2] for x in FAMS],width=.6)
    for i,v in enumerate(fail):ax[0,1].text(i,v+.17,f"{v:.2f}%",ha="center",fontsize=9)
    ax[0,1].set_xticks(range(5),labels)
    ax[0,1].set(ylabel="Task force-limit failures (%)",ylim=(0,max(fail)*1.2+.4),
                title="B  Failure taxonomy\nObserved task failures are force-limit violations")
    pair=(AS["metrics"][:,5]-AH["metrics"][:,5]).reshape(C["pairs"],-1).mean(1)*1000
    eff=S["effects"]["cost_gain_s"];lo,hi=np.array(eff["ci95"])*1000;v=eff["mean"]*1000
    ax[1,1].axis("off")
    ax[1,1].text(0,.91,"D  Added value of historical initialization",fontsize=12,weight="bold")
    ax[1,1].text(0,.68,f"{v:+.4f} ms",fontsize=29,color=COL["history"],weight="bold")
    ax[1,1].text(0,.51,f"Current − history completion time\n95% pair interval: [{lo:.4f}, {hi:.4f}] ms",fontsize=11)
    ax[1,1].text(0,.29,"Success difference: 0 percentage points\nPredeclared useful gain: 50 ms or 2 pp\nAll three frozen seeds give the same task-level result.",fontsize=11)
    ax[1,1].text(0,.05,"No meaningful action gain in this bridge.",fontsize=12,weight="bold",color=COL["history"])
    fig.suptitle("Physical prediction helps this controller; historical initialization adds no useful task gain")
    export(fig,"03_action_outcomes",
        "Does the predictive advantage change actual duration, quality, force peaks or failure types?",
        "All predictive methods complete every task within its force limit. History/current time difference is −0.0029 ms, below the preset useful-gain criterion. The fixed preload prefix is reported separately, not hidden in task safety.")

def next_step(tr,control):
    n=np.sum(np.isfinite(tr[:,0]));pred=np.full(n,np.nan);corr=np.zeros(n)
    for j in range(n-1):
        s=np.array([tr[j,12],tr[j,13],tr[j,7],tr[j,8]])
        s,_,_=advance(s,tr[j,1],tr[j+1,1],*control,FITTED,.01,10)
        pred[j+1]=max(0,FITTED[:3].sum()*s[0]-s[2:]@FITTED[1:3])
    for j in range(1,n):
        prior=material_observed(tr[j-1,7:9].copy(),tr[j-1,12],tr[j,12],FITTED)
        corr[j]=(tr[j,7:9]-prior)@FITTED[1:3]
    return pred,corr

def cases():
    chosen=[("history_state_11","History",COL["history"]),
            ("snapshot_state_11","Current",COL["snapshot"]),
            ("classical","Classical",COL["classical"]),
            ("reactive_005","Reactive",COL["reactive"])]
    for casei,case in enumerate(C["cases"]):
        h=case["pair_index"]*2+case["member"]
        ctrl=C["controllers"][case["controller_index"]];wait=C["waits"][case["wait_index"]];cap=C["caps"][case["cap_index"]]
        fig=plt.figure(figsize=(12.3,11.0),layout="constrained")
        grid=fig.add_gridspec(4,2,height_ratios=[.6,1,1,1])
        context=fig.add_subplot(grid[0,:])
        ax=np.array([[fig.add_subplot(grid[r+1,c]) for c in range(2)] for r in range(3)])
        prefix_t=np.arange(31)*.01
        # The separate context strip keeps every execution panel on the same clock.
        context.plot(np.arange(301)*.01-3,P["history"][h,:,3]*1000,color=".6",lw=1,label="Recorded command (mm)")
        context.plot(np.arange(301)*.01-3,P["history"][h,:,0]*1000,color=".2",lw=1,label="Recorded motion (mm)")
        force_axis=context.twinx()
        force_axis.plot(np.arange(301)*.01-3,P["history"][h,:,2],color="#916729",lw=1,label="Recorded force (N)")
        force_axis.set_ylabel("Force (N)",color="#916729");force_axis.grid(False)
        context.set(xlim=(-3,0),ylabel="Position (mm)",xlabel="Original history → encoding cut (s)",
            title="Frozen encoding context: the original 301 samples, used exactly once")
        context.legend(loc="upper left",fontsize=8,ncol=2)
        force_axis.legend(loc="upper right",fontsize=8)
        ax[0,0].plot(prefix_t,P["prefix_u"][h]*1000,color=".6",lw=1,ls="--")
        ax[0,0].plot(prefix_t,P["prefix_truth"][h,:,0]*1000,color=".2",lw=1)
        ax[0,1].plot(prefix_t,P["prefix_y"][h,:,2],color=".2",lw=1,label="Shared release truth")
        end=0
        for name,label,col in chosen:
            tr=load(f"raw/cases_{name}.npz")["traces"][casei]
            tr=tr[np.isfinite(tr[:,0])];tt=tr[:,0]+.3;end=max(end,tt[-1])
            ax[0,0].plot(tt,tr[:,1]*1000,color=col,lw=1.2,ls="--")
            ax[0,0].plot(tt,tr[:,2]*1000,color=col,lw=1.2,label=label)
            ax[0,1].plot(tt,tr[:,4],color=col,lw=1.5,label=label+" actual")
            rates=np.diff(tr[:,1])/.01*1000
            ax[2,1].step(tt[:-1],rates,where="post",color=col,lw=1.2,label=label)
            if name=="reactive_005":continue
            pred,corr=next_step(tr,ctrl)
            ax[0,1].plot(tt,pred,color=col,lw=1,ls=":",alpha=.85)
            zprefix=P["prefix_z_"+name][h]
            for k,a in [(0,ax[1,0]),(1,ax[1,1])]:
                a.plot(prefix_t,(zprefix[:,k]-P["prefix_truth"][h,:,k+2])*1000,color=col,lw=1.3)
                a.plot(tt,(tr[:,7+k]-tr[:,5+k])*1000,color=col,lw=1.3,label=label)
            cp=np.zeros(31)
            for j in range(1,31):
                prior=material_observed(zprefix[j-1].copy(),P["prefix_measured"][h,j-1,0],
                                        P["prefix_measured"][h,j,0],FITTED)
                cp[j]=(zprefix[j]-prior)@FITTED[1:3]
            ax[2,0].plot(prefix_t,cp,color=col,lw=1.1)
            ax[2,0].plot(tt,corr,color=col,lw=1.1,label=label)
            if name=="history_state_11":
                contact=tt[np.flatnonzero(tr[:,4]>.06)[0]]
        ax[0,1].hlines(cap,.3,end,color="black",ls="--",lw=.9,label="Task force limit")
        titles=["A  Command (dashed) and actual motion (solid)","B  Force and selected-command forecast",
                "C  Fast-mode state error","D  Slow-mode state error",
                "E  Online state correction in force units","F  Selected command velocity"]
        for a,title in zip(ax.flat,titles):
            a.set_title(title,loc="left")
            a.axvspan(0,.3,color=".5",alpha=.08)
            a.axvline(.3,color=".4",lw=.7,ls="--")
            a.axvline(.3+wait,color=".4",lw=.7,ls=":")
            a.axvline(contact,color="black",lw=.8,ls="-.")
            a.set_xlim(0,end)
            a.set_xlabel("Time since encoding cut (s)")
        ax[0,0].set_ylabel("Position / command (mm)")
        ax[0,1].set_ylabel("Force (N)")
        ax[1,0].set_ylabel("Estimated − actual z₁ (mm)")
        ax[1,1].set_ylabel("Estimated − actual z₂ (mm)")
        ax[2,0].set_ylabel("kᵀ(posterior − prior) (N)")
        ax[2,1].set_ylabel("Command rate (mm/s)")
        ax[0,0].legend(fontsize=7,ncol=3,loc="lower right")
        ax[0,1].legend(fontsize=7,ncol=2,loc="lower right")
        ax[2,1].legend(fontsize=8,ncol=2)
        fig.suptitle(f"Preselected case {casei+1}: pair {case['pair_index']}, member {case['member']} | "
                     f"K={ctrl[0]}, D={ctrl[1]}, wait={wait} s, cap={cap} N\n"
                     "Solid = actual; dotted force = next-10-ms forecast of the command already selected")
        export(fig,f"0{casei+4}_synchronized_case",
          "How do commands, responses, forecasts, state updates and action choices connect in one complete interaction?",
          "Case IDs were fixed before evaluation. Overlapping curves are retained: they show feedback convergence rather than an outcome-selected separation. Vertical markers: handoff, approach onset, first contact of the history method.")

if __name__=="__main__":
    transfer();feedback();outcomes();cases()
    (ROOT/"figures/manifest.json").write_text(json.dumps(MANIFEST,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Exported",len(MANIFEST),"figures as PNG, SVG and PDF.")

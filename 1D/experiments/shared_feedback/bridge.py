"""Frozen encoder bridge. All physics, MPC and observer formulas are reused."""
import os
os.environ.setdefault("NUMBA_NUM_THREADS", "4")
import sys, json, time, itertools, platform, hashlib
from pathlib import Path
import numpy as np
from numba import njit, prange, set_num_threads

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "vendor/round4"), str(ROOT / "vendor/round3")]
from physics import force, advance, rollout, observations, FITTED, TRUTH
from control import observer, episode as reference_episode, mpc_rate
from control_bridge import episode

C = json.loads((ROOT / "config.json").read_text())
R4 = json.loads((ROOT / "inputs/round4_contract.json").read_text())
set_num_threads(C["threads"])
METRICS = ["time_s", "peak_N", "complete", "unsafe", "safe_success", "cost_s",
           "excess_N", "dose_Ns", "first_contact_s", "state_rmse_m", "planning_calls"]
QUALITY = ["longest_hold_s", "final_hold_depth_rmse_mm", "final_hold_force_std_N",
           "final_hold_min_depth_mm", "contact_006_s"]

def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")

def load(name):
    return dict(np.load(ROOT / name))

def methods():
    return ["classical"] + [f"{m}_{seed}" for m in ["history_state", "snapshot_state"] for seed in C["seeds"]]

def pars():
    return np.array(R4["reactive"]["params"], float), R4["mpc"]["margin"], round(R4["mpc"]["horizon"]/.01)

@njit(cache=True)
def causal_filter(y, z0):
    """Identical online observer, including real release feedback."""
    n, T, _ = y.shape
    post = np.empty((n, T, 2)); pre = np.empty_like(post)
    finalP = np.empty((n, 2, 2))
    for b in range(n):
        z=z0[b].copy(); P=np.eye(2)*.0015**2
        positive=2 if y[b,0,2]>.06 and y[b,0,0]>0 else 0
        post[b,0]=z; pre[b,0]=z
        for j in range(1,T):
            from_force=y[b,j,2]; x=y[b,j,0]
            positive=positive+1 if from_force>.06 and x>0 else 0
            # Same observer called once without innovation for the diagnostic prior.
            zp,_=observer(z.copy(),P.copy(),y[b,j-1,0],x,from_force,FITTED,False)
            z,P=observer(z,P,y[b,j-1,0],x,from_force,FITTED,positive>=2)
            pre[b,j]=zp; post[b,j]=z
        finalP[b]=P
    return post,pre,finalP

# Explicit import outside compiled functions.
from physics import material_observed
@njit(cache=True)
def motion_filter(y,z0):
    out=np.empty((len(y),y.shape[1],2))
    for b in range(len(y)):
        z=z0[b].copy();out[b,0]=z
        for j in range(1,y.shape[1]):
            z=material_observed(z,y[b,j-1,0],y[b,j,0],FITTED)
            out[b,j]=z
    return out

def prepare():
    import torch
    from models import make_model
    from physics_base import ground_history, Material
    t0=time.perf_counter()
    cfg=json.loads((ROOT/"inputs/round3_config.json").read_text())
    mat=json.loads((ROOT/"inputs/fixed_material.json").read_text())["parameters"]
    d=load("inputs/test_histories.npz"); N=C["pairs"]
    assert np.all(np.diff(d["pair_ids"])>0)
    h=d["history"][:N].reshape(-1,301,5)
    initial=d["initial"][:N].reshape(-1,2); truthz=d["z"][:N].reshape(-1,2)
    assert np.array_equal(h[::2,-1],h[1::2,-1])
    assert np.all(h[:,-2:,2]>.06)
    assert np.allclose(h[...,4],.01)
    assert np.allclose(FITTED,np.array([mat["k_inf"],*mat["k"],*mat["tau"],cfg["plant"]["mass"]]),rtol=0,atol=1e-12)
    cut={"classical":ground_history(h,Material.from_dict(mat),.01)}
    encmeta=[]
    for name in methods()[1:]:
        model_name,seed=name.rsplit("_",1)
        meta=json.loads((ROOT/f"inputs/logs/{name}_meta.json").read_text())
        assert meta["converged"]
        model=make_model(model_name,cfg,mat).cuda()
        ck=torch.load(ROOT/f"inputs/checkpoints/{name}_best.pt",map_location="cuda",weights_only=False)
        model.load_state_dict(ck["model"]);model.eval()
        for par in model.parameters(): par.requires_grad_(False)
        assert np.allclose(model.scale.cpu().numpy(),[.006,.02,8.,.006,.01])
        assert np.allclose(model.constants[:6].cpu().numpy(),FITTED,rtol=0,atol=1e-12)
        torch.cuda.synchronize();start=time.perf_counter()
        with torch.inference_mode(): z=model.state(torch.from_numpy(h).cuda()).cpu().numpy().astype(float)
        torch.cuda.synchronize()
        assert np.all(np.isfinite(z))
        # The model head constrains the force-equivalent projection at a CONTACT cut.
        stress=np.maximum(FITTED[:3].sum()*h[:,-1,0]-h[:,-1,2],1e-6)
        assert np.max(np.abs(z@FITTED[1:3]-stress))<3e-6
        if model_name=="snapshot_state": assert np.array_equal(z[::2],z[1::2])
        cut[name]=z
        encmeta.append(dict(method=name,best_step=ck["step"],inference_seconds=time.perf_counter()-start,
                            parameters=sum(p.numel() for p in model.parameters()),converged=True))
    s0=np.column_stack([initial,truthz]);B=len(h)
    prefix_u=np.array([np.linspace(float(row[-1,3]),-.004,31,dtype=np.float64) for row in h])
    controls=np.tile([2200.,45.],(B,30,1))
    states,peaks=rollout(s0,prefix_u,controls,TRUTH,.01,10)
    y=observations(states);rng=np.random.default_rng(C["noise_seed"])
    prefix_noise=rng.normal(size=y.shape)*C["noise_std"]
    prefix_noise[:,0]=h[:,-1,:3]-y[:,0]
    measured=y+prefix_noise
    assert np.max(y[:,-1,2])<1e-9, "Expected detached handoff; do not silently change prefix."
    arrays=dict(history=h,cut_truth=s0,pair_ids=d["pair_ids"][:N],
                prefix_u=prefix_u,prefix_truth=states,prefix_y=y,prefix_measured=measured,
                prefix_peak=peaks.max(1),prefix_noise=prefix_noise)
    for name,z in cut.items():
        post,pre,P=causal_filter(measured,z)
        arrays["cut_"+name]=z; arrays["prefix_z_"+name]=post
        arrays["handoff_"+name]=post[:,-1];arrays["P_"+name]=P
    np.savez_compressed(ROOT/"raw/prepared.npz",**arrays)
    save("results/interface.json",dict(
        state_definition="z1,z2 Maxwell internal deformations in metres; frozen order",
        encoding="301x5 original in-contact histories; snapshot receives last 1x5 inside same architecture",
        normalization=[.006,.02,8.,.006,.01],all_parameters_frozen=True,
        endpoint_force_range_N=[float(h[:,-1,2].min()),float(h[:,-1,2].max())],
        detached_handoff_force_max_N=float(y[:,-1,2].max()),
        models=encmeta,prefix_feedback="same causal observer; no future measurements",
        history_numerics="stored round3 histories retained; RK4 starts at their stored cut, not retrospectively regenerated",
        seconds=time.perf_counter()-t0,gpu=torch.cuda.get_device_name(0)))
    print("PREPARED",B,"histories",flush=True)

def action_data():
    p=load("raw/prepared.npz")
    ids=np.array(list(itertools.product(range(2*C["pairs"]),range(3),range(3),range(3))),int)
    hi=ids[:,0]; n=len(ids)
    rng=np.random.default_rng(C["noise_seed"]+100000)
    noise=rng.normal(size=(n,436,3))*C["noise_std"]
    noise[:,0]=p["prefix_noise"][hi,-1]
    return p,dict(ids=ids,s=p["prefix_truth"][hi,-1],controls=np.array(C["controllers"],float)[ids[:,1]],
                  waits=np.array(C["waits"])[ids[:,2]],caps=np.array(C["caps"])[ids[:,3]],noise=noise)

@njit(cache=True,parallel=True)
def action_batch(s,z,P,ctrl,wait,cap,noise,params,margin,horizon,kind):
    B=len(s);met=np.empty((B,11));qual=np.full((B,5),np.nan)
    commands=np.full((B,436),np.nan,dtype=np.float32)
    for b in prange(B):
        a,tr=episode(s[b],z[b],ctrl[b,0],ctrl[b,1],wait[b],cap[b],noise[b],params,
                     margin,horizon,kind,True,10,10,True,P[b])
        met[b]=a; longest=0; count=0
        for j in range(len(tr)):
            if not np.isfinite(tr[j,0]): break
            commands[b,j]=tr[j,1]
            if tr[j,2]>=.004 and tr[j,4]>.02 and tr[j,0]>=wait[b]:
                count+=1
            else: count=0
            longest=max(longest,count)
            if np.isnan(qual[b,4]) and tr[j,4]>.06:qual[b,4]=tr[j,0]
        qual[b,0]=min(longest*.01,.2)
        if a[2]>0:
            end=int(round(a[0]/.01));sumsq=0.;mf=0.;depthmin=1e9
            for j in range(end-19,end+1):
                sumsq+=(tr[j,2]-.0041)**2;mf+=tr[j,4]/20;depthmin=min(depthmin,tr[j,2])
            vf=0.
            for j in range(end-19,end+1):vf+=(tr[j,4]-mf)**2/20
            qual[b,1]=np.sqrt(sumsq/20)*1000;qual[b,2]=np.sqrt(vf);qual[b,3]=depthmin*1000
    return met,qual,commands

def profile():
    p,d=action_data();params,margin,hor=pars();hi=d["ids"][:8,0]
    z=p["handoff_history_state_11"][hi];P=p["P_history_state_11"][hi]
    args=(d["s"][:8],z,P,d["controls"][:8],d["waits"][:8],d["caps"][:8],d["noise"][:8],params,margin,hor,1)
    t=time.perf_counter();action_batch(*args);jit=time.perf_counter()-t
    t=time.perf_counter();a=action_batch(*args);sec=time.perf_counter()-t
    # Only interface parity: identical P reproduces the unmodified fourth-round routine.
    s=d["s"][0];kw=(s,z[0],*d["controls"][0],d["waits"][0],d["caps"][0],d["noise"][0],
                      params,margin,hor,1,True,10,10,True)
    old=reference_episode(*kw);new=episode(*kw,np.eye(2)*.0015**2)
    assert np.array_equal(old[0],new[0])
    assert np.array_equal(old[1],new[1],equal_nan=True)
    est=sec/8*len(d["s"])*9
    save("results/profile.json",dict(warmup_and_compile_s=jit,warm_8_episodes_s=sec,
        projected_primary_seconds=est,episodes_per_method=len(d["s"]),methods=9,
        adapter_parity="exact metrics and traces with original covariance",
        python=sys.version,platform=platform.platform(),threads=C["threads"],training_seconds=0))
    print("PROFILE",sec/8*1000,"ms/episode amortized;",est,"s projected",flush=True)

def actions():
    p,d=action_data();params,margin,hor=pars();hi=d["ids"][:,0]
    runs=methods()+["reactive_005","reactive_030"]
    records=[]
    for name in runs:
        start=time.perf_counter()
        reactive=name.startswith("reactive")
        state="classical" if reactive else name
        pp=params.copy()
        if name=="reactive_030":
            tuning=json.loads((ROOT/"inputs/round4_reactive.json").read_text())
            selected=[r for r in tuning["by_margin"] if abs(r["params"][-1]-.30)<1e-10]
            assert len(selected)==1;pp=np.array(selected[0]["params"],float)
        a,q,u=action_batch(d["s"],p["handoff_"+state][hi],p["P_"+state][hi],
             d["controls"],d["waits"],d["caps"],d["noise"],pp,margin,hor,0 if reactive else 1)
        fullpeak=np.maximum(a[:,1],p["prefix_peak"][hi])
        np.savez_compressed(ROOT/f"raw/actions_{name}.npz",metrics=a,quality=q,commands=u,
                            ids=d["ids"],end_to_end_peak=fullpeak,prefix_peak=p["prefix_peak"][hi])
        # All case identities and checkpoint seed were frozen before inference.
        casetraces=[]
        for case in C["cases"]:
            target=[case["pair_index"]*2+case["member"],case["controller_index"],case["wait_index"],case["cap_index"]]
            ix=np.flatnonzero(np.all(d["ids"]==target,axis=1))[0]
            z=p["handoff_"+state][hi[ix]];P=p["P_"+state][hi[ix]]
            _,tr=episode(d["s"][ix],z,*d["controls"][ix],d["waits"][ix],d["caps"][ix],d["noise"][ix],
                        pp,margin,hor,0 if reactive else 1,True,10,10,True,P)
            casetraces.append(tr)
        np.savez_compressed(ROOT/f"raw/cases_{name}.npz",traces=np.array(casetraces))
        rec=dict(method=name,seconds=time.perf_counter()-start,mean_metrics=dict(zip(METRICS,a.mean(0).tolist())))
        records.append(rec);save("results/action_progress.json",records)
        print("ACTION",name,round(rec["seconds"],2),"seconds",flush=True)
    np.savez_compressed(ROOT/"raw/action_metadata.npz",ids=d["ids"],controls=d["controls"],waits=d["waits"],
                        caps=d["caps"])

@njit(cache=True,parallel=True)
def aligned_forecasts(states,measured,est,pre,commands,controls,contact,offsets):
    """At each origin only current noisy x,v and posterior z enter the model.

    Commands were fixed before the rollout. Future true responses are labels.
    """
    B=len(states);out=np.full((B,len(offsets),5),np.nan);futureF=np.empty((B,len(offsets),12))
    for b in prange(B):
        for k in range(len(offsets)):
            j=contact[b]+offsets[k]
            if j<0 or j+12>=states.shape[1]: continue
            model=np.array([measured[b,j,0],measured[b,j,1],est[b,j,0],est[b,j,1]])
            ef=0.;ex=0.
            for t in range(12):
                model,_,_=advance(model,commands[b,j+t],commands[b,j+t+1],
                    controls[b,j+t,0],controls[b,j+t,1],FITTED,.01,10)
                f=force(model,FITTED);futureF[b,k,t]=f
                ef+=(f-force(states[b,j+t+1],TRUTH))**2
                ex+=(model[0]-states[b,j+t+1,0])**2
            out[b,k,0]=np.sqrt(ef/12)
            out[b,k,1]=1000*np.sqrt(ex/12)
            out[b,k,2]=np.abs((est[b,j]-states[b,j,2:])@TRUTH[1:3])
            out[b,k,3]=1000*np.sqrt(np.mean((est[b,j]-states[b,j,2:])**2))
            out[b,k,4]=np.abs((est[b,j]-pre[b,j])@FITTED[1:3])
    return out,futureF

def diagnostic():
    p=load("raw/prepared.npz");ids=np.array(list(itertools.product(range(2*C["pairs"]),range(3),range(3))))
    hi=ids[:,0];B=len(ids);t=np.arange(round(C["diagnostic_seconds"]/.01)+1)*.01
    commands=[];controls=np.tile(np.array(C["controllers"],float)[ids[:,1],None,:],(1,len(t)-1,1))
    controls[:,:30]=[2200,45]
    for h,ci,wi in ids:
        w=C["waits"][wi]
        commands.append(np.interp(t,[0,.3,.3+w,.3+w+.2,t[-1]],
                                 [p["history"][h,-1,3],-.004,-.004,.0075,.0075]))
    commands=np.array(commands)
    commands[:,:31]=p["prefix_u"][hi]
    states,peak=rollout(p["cut_truth"][hi],commands,controls,TRUTH,.01,10)
    y=observations(states);rng=np.random.default_rng(C["noise_seed"]+200000)
    measured=y+rng.normal(size=y.shape)*C["noise_std"]
    # Release samples must be the exact same prefix already used for the action bridge.
    assert np.allclose(states[:,:31],p["prefix_truth"][hi],rtol=0,atol=1e-12)
    measured[:,:31]=p["prefix_measured"][hi]
    contact=31+np.argmax(y[:,31:,2]>.06,axis=1)
    assert np.all(y[np.arange(B),contact,2]>.06)
    offsets=np.arange(C["relative_ticks"][0],C["relative_ticks"][1]+1)
    np.savez_compressed(ROOT/"raw/diagnostic_inputs.npz",ids=ids,time=t,commands=commands,controls=controls,
                        states=states,measured=measured,contact=contact,offsets=offsets)
    records=[]
    for name in methods()+["history_state_11_noinnovation","snapshot_state_11_noinnovation"]:
        start=time.perf_counter();base=name.replace("_noinnovation","")
        z0=p["cut_"+base][hi]
        if name.endswith("noinnovation"):
            est=motion_filter(measured,z0);pre=est.copy()
        else:est,pre,_=causal_filter(measured,z0)
        aligned,forecast=aligned_forecasts(states,measured,est,pre,commands,controls,contact,offsets)
        # Original-cut prediction: no future observation, including during release.
        ini=np.column_stack([measured[:,0,:2],z0])
        pred,_=rollout(ini,commands,controls,FITTED,.01,10)
        predy=observations(pred,FITTED)
        cutrmse=np.array([np.sqrt(np.mean((predy[b,c:c+81,2]-y[b,c:c+81,2])**2))
                          for b,c in enumerate(contact)])
        # Save full common-input state trajectories and forecasts for reproducible figures.
        np.savez_compressed(ROOT/f"raw/diagnostic_{name}.npz",aligned=aligned,est=est,pre=pre,
                            cut_force_rmse=cutrmse,cut_prediction=predy,forecasts=forecast)
        rec=dict(method=name,seconds=time.perf_counter()-start,cut_force_rmse_mean_N=float(cutrmse.mean()))
        records.append(rec);save("results/diagnostic_progress.json",records)
        print("DIAGNOSTIC",name,round(rec["seconds"],2),"seconds",flush=True)

if __name__=="__main__":
    {"prepare":prepare,"profile":profile,"actions":actions,"diagnostic":diagnostic}[sys.argv[1]]()

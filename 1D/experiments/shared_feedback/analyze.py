"""Prespecified paired analysis; no condition or case selection from outcomes."""
import json, csv, hashlib
from pathlib import Path
import numpy as np
from bridge import ROOT,C,METRICS,QUALITY,methods,load,save

def interval(pair_values):
    v=np.asarray(pair_values,float)
    assert len(v)==C["pairs"] and np.all(np.isfinite(v))
    rng=np.random.default_rng(C["bootstrap_seed"])
    ix=rng.integers(len(v),size=(C["bootstrap_samples"],len(v)))
    return dict(mean=float(v.mean()),ci95=np.quantile(v[ix].mean(1),[.025,.975]).tolist())

def pair_mean(v):
    return np.asarray(v).reshape(C["pairs"],-1).mean(1)

def run():
    names=methods()+["reactive_005","reactive_030"]
    action={n:load(f"raw/actions_{n}.npz") for n in names}
    hist=np.stack([action[f"history_state_{s}"]["metrics"] for s in C["seeds"]])
    snap=np.stack([action[f"snapshot_state_{s}"]["metrics"] for s in C["seeds"]])
    rows=[]
    for name,d in action.items():
        a=d["metrics"];q=d["quality"];caps=np.array(C["caps"])[d["ids"][:,3]]
        row={"method":name,**dict(zip(METRICS,a.mean(0).tolist())),
             "completed_time_s":float(a[a[:,2]>0,0].mean()) if np.any(a[:,2]>0) else None,
             "safe_completed_time_s":float(a[a[:,4]>0,0].mean()) if np.any(a[:,4]>0) else None,
             "hold_depth_rmse_mm":float(np.nanmean(q[:,1])),
             "hold_force_std_N":float(np.nanmean(q[:,2])),
             "longest_hold_mean_s":float(q[:,0].mean()),
             "failure_complete_over_limit":int(np.sum((a[:,2]>0)&(a[:,3]>0))),
             "failure_timeout_only":int(np.sum((a[:,2]==0)&(a[:,3]==0))),
             "failure_timeout_and_over_limit":int(np.sum((a[:,2]==0)&(a[:,3]>0))),
             "prefix_already_over_cap":int(np.sum(d["prefix_peak"]>caps)),
             "end_to_end_success_fraction":float(np.mean((a[:,2]>0)&(d["end_to_end_peak"]<=caps)))}
        rows.append(row)
    gain=(snap[:,:,5]-hist[:,:,5]).mean(0)
    success=(hist[:,:,4]-snap[:,:,4]).mean(0)*100
    unsafe=(hist[:,:,3]-snap[:,:,3]).mean(0)*100
    effect={"cost_gain_s":interval(pair_mean(gain)),
            "safe_success_gain_pp":interval(pair_mean(success)),
            "over_limit_change_pp":interval(pair_mean(unsafe)),
            "seed_cost_gain_ms":{str(s):float(np.mean(snap[i,:,5]-hist[i,:,5])*1000)
                                 for i,s in enumerate(C["seeds"])}}
    mask=(hist[:,:,4]>0)&(snap[:,:,4]>0)
    delta=(snap[:,:,0]-hist[:,:,0])
    nums=np.sum(np.where(mask,delta,0).reshape(3,C["pairs"],-1),axis=(0,2))
    dens=np.sum(mask.reshape(3,C["pairs"],-1),axis=(0,2))
    rng=np.random.default_rng(C["bootstrap_seed"])
    ix=rng.integers(C["pairs"],size=(C["bootstrap_samples"],C["pairs"]))
    weighted=nums[ix].sum(1)/dens[ix].sum(1)
    effect["both_successful_time_gain_s"]={
        "mean":float(nums.sum()/dens.sum()),"ci95":np.quantile(weighted,[.025,.975]).tolist(),
        "paired_seed_branch_count":int(dens.sum())}
    effect["classical_minus_history_cost_s"]=interval(pair_mean(
        (action["classical"]["metrics"][:,5][None]-hist[:,:,5]).mean(0)))
    effect["meaningful"]=(effect["cost_gain_s"]["mean"]>=.05 or effect["safe_success_gain_pp"]["mean"]>=2)\
        and effect["over_limit_change_pp"]["mean"]<=0

    # Differences in real closed-loop actions, restricted to the interval while both tasks run.
    ref=action["classical"]["quality"][:,4]
    actiondiff=[]
    for si,seed in enumerate(C["seeds"]):
        uh=action[f"history_state_{seed}"]["commands"]
        us=action[f"snapshot_state_{seed}"]["commands"]
        du=np.abs(uh-us)
        rate=np.abs(np.diff(uh,axis=1)-np.diff(us,axis=1))/.01
        t=np.arange(rate.shape[1])*.01
        both=(t[None]<np.minimum(hist[si,:,0],snap[si,:,0])[:,None])
        valid=np.isfinite(rate)&both
        changed=(rate>=C["action_rate_difference_m_s"]-1e-8)&valid
        r={"seed":seed,"max_command_difference_mm":float(np.nanmax(du)*1000),
           "any_command_difference_ge_0p1mm_fraction":float(np.mean(np.nanmax(du,axis=1)>=.0001)),
           "any_rate_difference_fraction":float(np.mean(changed.any(1)))}
        for lo,hi,label in [(-10,0,"precontact"),(0,.1,"first_100ms"),(.1,.5,"100_to_500ms"),(.5,10,"after_500ms")]:
            window=(t[None]>=ref[:,None]+lo)&(t[None]<ref[:,None]+hi)&valid
            z=changed&window
            r[label+"_tick_fraction"]=float(z.sum()/max(window.sum(),1))
            r[label+"_episode_fraction"]=float(np.mean(z.any(1)))
        actiondiff.append(r)

    diag={n:load(f"raw/diagnostic_{n}.npz") for n in methods()+[
        "history_state_11_noinnovation","snapshot_state_11_noinnovation"]}
    dh=np.stack([diag[f"history_state_{s}"]["aligned"] for s in C["seeds"]]).mean(0)
    ds=np.stack([diag[f"snapshot_state_{s}"]["aligned"] for s in C["seeds"]]).mean(0)
    dd=load("raw/diagnostic_inputs.npz");rel=dd["offsets"]*.01
    curvegap=ds[:,:,0]-dh[:,:,0]
    curve=curvegap.mean(0)
    dwell=round(C["gap_persistence_seconds"]/.01)+1
    contraction=None
    for i in np.flatnonzero(rel>=0):
        if i+dwell<=len(rel) and np.all(np.abs(curve[i:i+dwell])<=C["gap_small_N"]):
            contraction=float(rel[i]);break
    pred={"aligned_time_s":rel.tolist(),"gap_contraction_s":contraction,
          "gap_definition":"mean per-rollout force RMSE(snapshot)-RMSE(history), 120 ms known-command forecast",
          "by_method":{},"paired_forecast_advantage_N":{}}
    for name,d in diag.items():
        pred["by_method"][name]={"original_cut_recontact_rmse_N":float(d["cut_force_rmse"].mean()),
            "at_relative_time":{str(t):dict(zip(
                ["force_rmse_N","position_rmse_mm","state_projection_error_N","state_rmse_mm","correction_projection_N"],
                d["aligned"][:,int(round(t/.01))-C["relative_ticks"][0]].mean(0).tolist()))
                for t in C["report_relative_seconds"]}}
    for t in C["report_relative_seconds"]:
        k=int(round(t/.01))-C["relative_ticks"][0]
        pred["paired_forecast_advantage_N"][str(t)]=interval(pair_mean(curvegap[:,k]))
    condition=[]
    for ci in range(3):
        for wi in range(3):
            aid=action["classical"]["ids"]
            amask=(aid[:,1]==ci)&(aid[:,2]==wi)
            dmask=(dd["ids"][:,1]==ci)&(dd["ids"][:,2]==wi)
            condition.append(dict(controller=C["controller_names"][ci],wait_s=C["waits"][wi],
                precontact_force_gain_N=float(curvegap[dmask,8].mean()),
                cost_gain_ms=float(gain[amask].mean()*1000),
                success_gain_pp=float(success[amask].mean())))

    # Minimal trusted-result checks: provenance, declared matrix and observed interfaces.
    provenance=json.loads((ROOT/"results/input_provenance.json").read_text())
    preserved=all(hashlib.sha256(Path(r["source"]).read_bytes()).hexdigest()==r["sha256"] for r in provenance)
    frozen=json.loads((ROOT/"results/preregistered_hashes.json").read_text())
    contract_ok=all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
    assert preserved and contract_ok
    for d in action.values():
        assert d["metrics"].shape==(2*C["pairs"]*27,11)
        assert np.all(np.isfinite(d["metrics"]))
        assert np.array_equal(d["ids"],action["classical"]["ids"])
    assert np.all(np.isfinite(dh)) and np.all(np.isfinite(ds))
    save("results/qa.json",dict(original_artifacts_unchanged=preserved,contract_unchanged=contract_ok,
        all_predicted_forecast_origins_finite=True,all_action_metrics_finite=True,
        branches_per_method=len(gain),methods=len(action),pairs=C["pairs"],
        prefix_precision_fix="first attempt archived; canonical float64 prefix reused in all analyses",
        controller_changes="optional covariance input only; parity test exact",
        no_training=True,no_controller_retuning=True))
    with (ROOT/"results/episode_metrics.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f)
        writer.writerow(["method","pair_index","member","controller_index","wait_index","cap_index",
                         *METRICS,*QUALITY,"prefix_peak_N","end_to_end_peak_N"])
        for name,d in action.items():
            for ids,a,q,pp,ep in zip(d["ids"],d["metrics"],d["quality"],d["prefix_peak"],d["end_to_end_peak"]):
                writer.writerow([name,ids[0]//2,ids[0]%2,*ids[1:],*a,*q,pp,ep])
    save("results/summary.json",dict(actions=rows,effects=effect,action_differences=actiondiff,
        prediction=pred,conditions=condition,units=dict(
            independent="64 history pairs; model seeds averaged within pair for primary intervals",
            original_cut="forecast before any new release/press feedback; score first 0.8 s after recontact",
            task_time="from handoff, includes waiting; shared 0.3 s prefix adds equally to actual elapsed time",
            cost="success-within-cap completion time, else 5 s; not raw elapsed time",
            cap_scope="round4 task horizon; prefix peak and end-to-end outcome separately reported")))
    print(json.dumps({"effects":effect,"gap_contraction_s":contraction,
                      "precontact_advantage":pred["paired_forecast_advantage_N"]["-0.02"]},indent=2))

if __name__=="__main__":run()

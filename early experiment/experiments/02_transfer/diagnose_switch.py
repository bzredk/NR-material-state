"""Explain the initial diagnostic run; never remove an unsafe interval from results."""
import json
import numpy as np
from experiment import ROOT,save
from evaluate import build_context,predict

cfg=json.loads((ROOT/'config.json').read_text());out=ROOT/'runs'/'transfer_v1'
d=dict(np.load(out/'data'/'test_histories.npz'));ctx=build_context(cfg,d)
y,_=predict(cfg,out,d,ctx,'oracle',0);s=ctx['shape'];p=round(.3/cfg['dt'])
prefix=np.max(y[:,:p,2],1).reshape(s);after=np.max(y[:,p:,2],1).reshape(s)
truth=dict(np.load(out/'metrics'/'truth.npz'));caps=np.array(cfg['force_limits'])
initial_blocks=np.all(prefix[...,None]>caps,axis=-2)
post_feasible=np.any((after[...,None]<=caps-cfg['planning_force_margin'])&np.isfinite(truth['time'][...,None]),axis=-2)
save(out/'switch_diagnostic.json',dict(
    fraction_of_branches_with_global_peak_in_first_0p3s=(prefix>=after).mean((0,1,3,4)).tolist(),
    median_prefix_peak_by_controller_N=np.median(prefix,axis=(0,1,3,4)).tolist(),
    median_recontact_peak_by_controller_N=np.median(after,axis=(0,1,3,4)).tolist(),
    fraction_decisions_blocked_by_initial_switch_despite_recontact_feasible=float((initial_blocks&post_feasible)[:,:,4:].mean()),
    note='Post-release force is diagnostic only; original reported safety checks the entire horizon.'))
print((out/'switch_diagnostic.json').read_text())

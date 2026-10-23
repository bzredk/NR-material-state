import json
import numpy as np
from plot_results import ROOT,OUT,FIG,CFG,all_runs,mean_metric
from experiment import save

by_control={}
for name in ['classical_integral','local_observer','snapshot_state','history_state','history_single','gru_contact']:
    e=mean_metric(name,'force_mse');cost=mean_metric(name,'decision_cost');unsafe=mean_metric(name,'decision_unsafe')
    by_control[name]=[dict(control=c,force_rmse_N=float(np.sqrt(e[:,:,j].mean())),cost_s=float(cost[:,:,j].mean()),
                          unsafe=float(unsafe[:,:,j].mean())) for j,c in enumerate(CFG['controllers_test'])]
gain=(mean_metric('snapshot_state','decision_cost')-mean_metric('history_state','decision_cost')).mean((0,1,4))
case=json.loads((FIG/'case_source.json').read_text());trace={}
for n,t in case['trace'].items():
    actual=np.asarray(t['truth']);pred=np.asarray(t['prediction'])
    trace[n]=dict(action=case['choices'][n],actual_peak=float(actual[:,2].max()),predicted_peak=float(pred[:,2].max()),
                  actual_goal_time=t['first_goal_time_s'])
metas=[json.loads(p.read_text()) for p in (OUT/'logs').glob('*_meta.json')]
parent_metas=[json.loads(p.read_text()) for p in (ROOT.parent/'runs'/'transfer_v1'/'logs').glob('*_meta.json')]
mat=json.loads((ROOT/'fixed_material.json').read_text())['parameters'];k=np.array(mat['k']);tau=np.array(mat['tau'])
A=np.diag(1/tau)@(np.ones((2,1))*k[None,:]/(mat['k_inf']+k.sum())-np.eye(2))
save(OUT/'research_summary.json',dict(by_controller=by_control,controller_wait_history_gain_s=gain.tolist(),
    case={k:v for k,v in case.items() if k not in ['trace','states']},case_trace_summary=trace,
    free_recovery_time_constants_s=sorted((-1/np.linalg.eigvals(A)).tolist()),
    main_training_seconds=sum(m['seconds'] for m in metas),diagnostic_training_seconds=sum(m['seconds'] for m in parent_metas),
    main_max_allocated_MiB=max(m['peak_allocated_MiB'] for m in metas),
    main_update_range=[min(m['steps'] for m in metas),max(m['steps'] for m in metas)],
    independent_units=128,heldout_decisions_per_model_seed=128*2*3*3*len(CFG['force_limits']),
    paired_response_signal_RMS_N=float(np.sqrt(all_runs('history_state')[0]['contrast_signal'][:,4:].mean()))))
print((OUT/'research_summary.json').read_text())

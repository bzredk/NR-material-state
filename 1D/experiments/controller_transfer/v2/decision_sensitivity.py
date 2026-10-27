"""Post-evaluation size-of-effect diagnostics; never change selected actions."""
import json
import numpy as np
from experiment import ROOT,save
from plot_results import OUT,CFG,all_runs

caps=np.array(CFG['force_limits']);records={}
for name in ['snapshot_state','history_state','gru_contact','reactive_safe']:
    rr=all_runs(name);peak=np.stack([r['decision_peak'][:,:,4:] for r in rr]);time=np.stack([r['decision_time'][:,:,4:] for r in rr])
    excess=peak-caps;valid=np.isfinite(peak);violations=excess[valid&(excess>0)]
    records[name]={'violation_excess_quantiles_N':np.quantile(violations,[.1,.5,.9,1]).tolist() if len(violations) else [],
        'fractions_exceeding_by_N':{str(e):float(np.mean(valid&(excess>e))) for e in [0,.02,.05,.1]},
        'cost_with_evaluation_tolerance_s':{str(e):float(np.where(valid&np.isfinite(time)&(excess<=e),time,6.).mean()) for e in [0,.02,.05,.1]}}
r=all_runs('reactive_safe')[0];paired=[]
for h in all_runs('history_state'):
    mask=h['decision_success'][:,:,4:]&r['decision_success'][:,:,4:]
    paired.append({'same_successful_task_count':int(mask.sum()),'history_time_advantage_s':float((r['decision_time'][:,:,4:]-h['decision_time'][:,:,4:])[mask].mean())})
save(OUT/'decision_sensitivity.json',dict(status='diagnostic after main evaluation; selected actions and primary strict-cap results unchanged',
    methods=records,history_vs_reactive_on_shared_successes=paired,
    interpretation='Nonzero tolerance is sensitivity analysis, not permission to exceed the original cap. Conditional success speed is not an overall success comparison.'))
print((OUT/'decision_sensitivity.json').read_text())

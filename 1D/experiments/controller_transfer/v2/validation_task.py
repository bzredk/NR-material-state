"""Check task feasibility using validation histories and TRAIN controllers only."""
import json
import numpy as np
from experiment import ROOT,save
from dataset import load
from evaluate import build_context,predict,summary_metrics,decision_metrics

cfg=json.loads((ROOT/'config.json').read_text());out=ROOT/'runs'/'transfer_v2'
cfg['controllers_test']=cfg['controllers_train'];d=load(out/'data','val')
d={k:v[:24] for k,v in d.items() if k in ['history','initial','z','pair_ids']}
context=build_context(cfg,d);truth,_=predict(cfg,out,d,context,'oracle',0)
m=summary_metrics(cfg,context,truth,truth);r=decision_metrics(cfg,m,m)
records=[]
for i,a in enumerate(cfg['actions']):
    records.append(dict(action=a['name'],peak_quantiles=np.quantile(m['peak'][...,i],[0,.5,1]).tolist(),
          time_quantiles=np.quantile(m['time'][...,i],[0,.5,1]).tolist(),
          selected_fraction=float(np.mean(r['choice']==i))))
save(out/'validation_task_profile.json',dict(source='first 24 validation pairs, four training controllers',
    actions=records,oracle_success=float(r['success'].mean()),oracle_reject=float(r['reject'].mean()),
    force_limits=cfg['force_limits'],goal=cfg['goal_position'],frozen_config=True))
print(json.dumps(records,indent=2))


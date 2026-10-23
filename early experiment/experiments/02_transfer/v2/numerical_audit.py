"""Finer future integration, holding the decision-time physical state fixed.

This is a discretization audit, not a new physical history experiment. It does
not claim the matched endpoint survives replaying the entire past at finer dt.
"""
import json
import numpy as np
from experiment import ROOT,save
from dataset import load
from dynamics import simulate
from evaluate import build_context
from actions import response_metrics,outcomes


def audit():
    cfg=json.loads((ROOT/'config.json').read_text());out=ROOT/'runs'/'transfer_v2'
    d=dict(np.load(out/'data'/'test_histories.npz'));d={k:v[:16] for k,v in d.items()};ctx=build_context(cfg,d)
    coarse=dict(np.load(out/'metrics'/'truth.npz'));shape=ctx['shape'];records=[]
    for factor in [2,4]:
        finecfg=dict(cfg,dt=cfg['dt']/factor);T=ctx['u'].shape[1];t=np.arange(T+1)*cfg['dt'];tf=np.arange(1,T*factor+1)*finecfg['dt']
        uf=np.stack([np.interp(tf,t,np.r_[h[-1,3],u]) for h,u in zip(ctx['h'],ctx['u'])])
        y=simulate(ctx['z'],ctx['initial'],uf,ctx['ctrl'],cfg['truth'],finecfg)
        time,peak=response_metrics(y,ctx['onsets'],finecfg['dt'],cfg['goal_position'],cfg['goal_hold_seconds'])
        time=time.reshape(shape);peak=peak.reshape(shape)
        result={}
        for name in ['oracle','classical_integral','local_observer','snapshot_state','history_state','history_single','gru_contact']:
            seed=11 if name in ['snapshot_state','history_state','history_single','gru_contact'] else 0
            m=dict(np.load(out/'metrics'/f'{name}_{seed}.npz'));choice=m['decision_choice'][:16]
            rs=[outcomes(choice[...,l],time,peak,cap,cfg['future_seconds']) for l,cap in enumerate(cfg['force_limits'])]
            result[name]={k:float(np.stack([r[k] for r in rs],-1)[:,:,4:].mean()) for k in ['cost','success','unsafe']}
        rec=dict(factor=factor,dt=finecfg['dt'],peak_shift_mean_N=float(np.mean(peak-coarse['peak'][:16])),
                 peak_shift_max_abs_N=float(np.max(np.abs(peak-coarse['peak'][:16]))),decision_outcomes=result)
        records.append(rec)
        np.savez_compressed(out/f'numerical_factor{factor}.npz',time=time,peak=peak)
    save(out/'numerical_audit.json',dict(first_test_pairs=16,controls='all seven',future_only_refinement=True,
        past_replayed_at_finer_dt=False,initial_state='same physical decision-time state',records=records))
    print(json.dumps(records,indent=2))


if __name__=='__main__':audit()


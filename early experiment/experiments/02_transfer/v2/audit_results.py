import hashlib,json,platform,time
from pathlib import Path
import numpy as np
from experiment import ROOT,save
from models import MODEL_NAMES


def main():
    cfg=json.loads((ROOT/'config.json').read_text());out=ROOT/'runs'/'transfer_v2'
    train=dict(np.load(out/'data'/'train.npz'));val=dict(np.load(out/'data'/'val.npz'));test=dict(np.load(out/'data'/'test_histories.npz'))
    splits=[set(d['pair_ids'].tolist()) for d in [train,val,test]]
    assert not splits[0]&splits[1] and not splits[0]&splits[2] and not splits[1]&splits[2]
    assert all(np.array_equal(d['history'][:,0,-1],d['history'][:,1,-1]) for d in [train,val,test])
    metas=[json.loads((out/'logs'/f'{n}_{s}_meta.json').read_text()) for n in MODEL_NAMES for s in cfg['seeds']]
    assert all(m['converged'] for m in metas)
    oracle=dict(np.load(out/'metrics'/'oracle_0.npz'));assert np.max(oracle['force_mse'])==0
    assert not oracle['decision_unsafe'].any()
    snap=dict(np.load(out/'metrics'/'snapshot_state_11.npz'))
    np.testing.assert_allclose(snap['contrast_mse'],snap['contrast_signal'],rtol=1e-8,atol=1e-14)
    # Selection is reconstructed from saved PREDICTED responses, never true outcomes.
    from actions import select
    for name in MODEL_NAMES:
        for seed in cfg['seeds']:
            m=dict(np.load(out/'metrics'/f'{name}_{seed}.npz'))
            choices=np.stack([select(m['time'],m['peak'],cap,cfg['planning_force_margin']) for cap in cfg['force_limits']],-1)
            np.testing.assert_array_equal(choices,m['decision_choice'])
            assert m['decision_regret'].min()>=-1e-9
    save(out/'final_audit.json',dict(disjoint_history_splits=True,identical_present_within_pairs=True,
       no_future_measurement_input=True,selector_reconstructed_from_predictions=True,
       all_training_converged=True,training_seconds=sum(m['seconds'] for m in metas),
       peak_allocated_MiB=max(m['peak_allocated_MiB'] for m in metas),runs=metas,
       paired_endpoint_max_difference=test['endpoint_mismatch'].max(0).tolist(),
       main_limitations=['one known two-mode Maxwell material','single history-generation controller','deterministic known actuator',
          'synthetic matched histories','finite candidate catalog and fixed force-cap sweep','no real robot data']))
    files=[p for p in ROOT.glob('*.py')]+[ROOT/'config.json',ROOT/'eval.json',ROOT/'fixed_material.json']
    save(ROOT/'source_hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    print('AUDIT_OK',len(metas),'converged model-seed runs')


if __name__=='__main__':main()


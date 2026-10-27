"""Check the archived claims and convergence records without modifying results."""
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / 'experiments'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main():
    r2 = EXP/'history_dependence/runs/round2_v1'
    r3 = EXP/'controller_transfer/v2/runs/transfer_v2'
    bridge = EXP/'shared_feedback'
    a = read(r2/'summary.json')
    assert a['snapshot_state/test_wait']['paired_effect_NRMSE']['mean'] == 1
    assert a['history_state/test_wait']['paired_effect_NRMSE']['mean'] < 0.5
    assert a['classical_integral/test_wait']['force_rmse_N']['mean'] < a['history_state/test_wait']['force_rmse_N']['mean']
    for run in [r2, r3]:
        records = [read(p) for p in (run/'logs').glob('*_meta.json')]
        assert len(records) == 12
        assert all(m['converged'] for m in records)
        assert len(list((run/'checkpoints').glob('*_best.pt'))) == 12
    for method in ['history_state', 'snapshot_state']:
        for seed in [11, 23, 47]:
            name = f'{method}_{seed}_best.pt'
            assert hashlib.sha256((r3/'checkpoints'/name).read_bytes()).digest() == hashlib.sha256((bridge/'inputs/checkpoints'/name).read_bytes()).digest()
    effects = read(bridge/'results/summary.json')['effects']
    for item in read(bridge/'results/input_provenance.json'):
        assert hashlib.sha256((bridge/item['snapshot'].replace('\\','/')).read_bytes()).hexdigest()==item['sha256']
    for name,expected in read(bridge/'results/preregistered_hashes.json').items():
        assert hashlib.sha256((bridge/name.replace('\\','/')).read_bytes()).hexdigest()==expected
    assert effects['safe_success_gain_pp']['mean'] == 0
    assert effects['meaningful'] is False
    assert abs(effects['cost_gain_s']['mean']) < 1e-5
    rows = read(r3/'summary.json')['rows']
    family_rms = {name: math.sqrt(sum(r['force_rmse']**2 for r in rows if r['model']==name)/sum(r['model']==name for r in rows))
                  for name in ['history_state','snapshot_state','classical_integral','local_observer']}
    print(json.dumps({'history_dependence_paired_nrmse':a['history_state/test_wait']['paired_effect_NRMSE']['mean'],
                      'controller_transfer_force_rmse_N':family_rms,
                      'shared_feedback_success_gain_pp':effects['safe_success_gain_pp']['mean'],
                      'converged_primary_training_runs':24,
                      'frozen_bridge_checkpoints_match':6},indent=2))

if __name__ == '__main__':
    main()

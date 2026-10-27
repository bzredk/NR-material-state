"""Compare the refactored observer with the published implementation."""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys
import time

import numpy as np

from nr2d.estimators import ObserverConfig, compare_predictions
from nr2d.experiments import ROOT, environment, write_json
from nr2d.physics import Config, SpatialModel, Trace

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=ROOT / 'runs/implementation_checks/observer_config')
args = parser.parse_args()
run = ROOT / 'runs/2d_contact/pilot_c9dd23016896'
reference_path = run / 'source/estimators.py'
spec = importlib.util.spec_from_file_location('nr2d._published_estimators', reference_path)
reference = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = reference
spec.loader.exec_module(reference)
started = time.perf_counter()
record = {
    'status': 'running', 'scope': 'Numerical regression; no new scientific comparison',
    'reference': reference_path.relative_to(ROOT).as_posix(),
    'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
    'observer_config': ObserverConfig().asdict(), 'environment': environment(), 'cases': [],
}
try:
    for parent, action, noise in [('test_300', 'Slow press', 0.), ('test_301', 'Fast press', 1.)]:
        trace = Trace.load(run / 'histories' / (parent + '.npz'))
        legacy, legacy_metrics = reference.compare_predictions(SpatialModel(Config(**trace.config)), trace, action, noise)
        current, current_metrics = compare_predictions(SpatialModel(Config(**trace.config)), trace, action, noise)
        case = {'parent': parent, 'action': action, 'noise': noise, 'methods': {}}
        for method, prediction in current.items():
            errors = {}
            for channel in ('u', 'z', 'd', 'v', 'force', 'markers'):
                expected, actual = getattr(legacy[method], channel), getattr(prediction, channel)
                errors[channel] = float(np.max(np.abs(actual - expected)))
                np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-14)
            for metric in ('force_rmse_N', 'marker_rmse_m'):
                np.testing.assert_allclose(current_metrics[method][metric], legacy_metrics[method][metric],
                                           rtol=1e-12, atol=1e-14)
            case['methods'][method] = {'max_abs_difference': errors,
                                       'force_rmse_N': current_metrics[method]['force_rmse_N'],
                                       'marker_rmse_m': current_metrics[method]['marker_rmse_m']}
        record['cases'].append(case)
        print(parent, action, noise, 'passed', flush=True)
    record['status'] = 'passed'
finally:
    if record['status'] != 'passed':
        record['status'] = 'failed'
    record['wall_seconds'] = time.perf_counter() - started
    write_json(args.output / 'numerical_regression.json', record)
print(args.output / 'numerical_regression.json')

"""Sensor and contact-history comparisons on one fixed spatial contact model."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import argparse
import csv
import hashlib
import json
import shutil
import time
import traceback

import numpy as np

from .physics import Config, SpatialModel, Trace
from .estimators import Observer, ObserverConfig, Estimate, NOISE_STD
from .protocols import protocol, future_commands
from .experiments import ROOT, read_json, write_json, environment, history_parameters


def method_key(lateral, window):
    return ('lateral' if lateral else 'basic') + '_' + str(window)


def conditions(spec):
    return [(method_key(side, window), side, window)
            for window in [*spec['windows_seconds'], 'contact'] for side in (False, True)]


def seed_for(spec, parent, repeat):
    return int(np.random.SeedSequence([spec['noise_root_seed'], parent, repeat]).generate_state(1)[0])


def contact_end(observed, dt, duration, threshold):
    """Last continuous above-threshold interval long enough for the update."""
    contact = observed[:, 2] > threshold
    count = 0
    end = None
    required = round(duration / dt) + 1
    for index, active in enumerate(contact):
        count = count + 1 if active else 0
        if count >= required:
            end = index
    if end is None:
        raise ValueError('No observed contact segment long enough for the requested update')
    return end


def coverage(trace, observed, begin, end, threshold):
    phase_seconds = {}
    for phase in np.unique(trace.phase[begin + 1:end + 1]):
        phase_seconds[str(phase)] = float(np.sum(
            np.diff(trace.time[begin:end + 1])[trace.phase[begin + 1:end + 1] == phase]))
    detected = observed[begin:end + 1, 2] > threshold
    return {'phase_seconds': phase_seconds,
            'observed_contact_samples': int(detected.sum()),
            'update_sample_count': end - begin + 1,
            'observed_contact_seconds': float(np.sum(np.diff(trace.time[begin:end + 1]) * detected[1:]))}


def infer_condition(observer, trace, observed, window, spec):
    end = None
    duration = window
    if window == 'contact':
        duration = spec['contact_window_seconds']
        end = contact_end(observed, observer.model.c.dt, duration, spec['contact_threshold_N'])
    estimate = observer.infer(trace, duration, observed, update_end=end)
    stop = len(trace.time) - 1 if end is None else end
    begin = stop - min(stop, round(duration / observer.model.c.dt))
    estimate.diagnostics.update(coverage(trace, observed, begin, stop, spec['contact_threshold_N']))
    if window == 'contact':
        estimate.diagnostics['contact_selection'] = {
            'channel': 'observed force', 'threshold_N': spec['contact_threshold_N'],
            'scanned_interval_s': [float(trace.time[0]), float(trace.time[-1])],
            'rule': 'last continuous segment above threshold; no simulator contact labels',
        }
    return estimate


def audit_trace(trace, limits):
    peak = trace.diagnostics.max(axis=0)
    return {'max_body_balance_N': float(peak[0]), 'max_tool_balance_N': float(peak[1]),
            'max_penetration_m': float(peak[2]), 'max_strain': float(peak[3]),
            'passed': bool(max(peak[:2]) <= limits['balance_N'] and
                           peak[2] <= limits['penetration_m'] and peak[3] <= limits['strain'])}


def prepare_histories(run, spec, split):
    model = SpatialModel(Config(**read_json(run / 'physics.json')))
    entries = []
    for seed in spec[split + '_seeds']:
        parent = f'{split}_{seed}'
        path = run / 'histories' / f'{parent}.npz'
        entry = {'id': parent, 'seed': seed, 'split': split}
        started = time.perf_counter()
        try:
            if path.exists():
                trace = Trace.load(path)
            else:
                parameters = history_parameters(seed)
                commands, phases, _ = protocol(model.c, **parameters)
                trace = model.simulate(commands, phases, metadata={**entry, 'parameters': parameters})
                trace.save(path)
            entry['physics'] = audit_trace(trace, spec['physics_limits'])
            for action in spec['actions']:
                target = run / 'truth' / f'{parent}_{action.replace(" ", "_")}.npz'
                if not target.exists():
                    commands, phases = future_commands(trace.checkpoint(), model.c, action)
                    future = model.simulate(commands, phases, state=trace.checkpoint())
                    np.savez_compressed(target, time=future.time, command=future.command,
                                        force=future.force, markers=future.markers, d=future.d, v=future.v,
                                        audit=json.dumps(audit_trace(future, spec['physics_limits'])))
            entry['status'] = 'completed'
        except Exception as exc:
            entry.update(status='failed', error=str(exc), traceback=traceback.format_exc())
        entry['wall_seconds'] = time.perf_counter() - started
        entries.append(entry)
    write_json(run / f'{split}_histories.json', entries)
    return entries


def evaluate_job(job, progress=None):
    run, parent, repeat, settings, output, actions, noise = job
    run, output = Path(run), Path(output)
    if (output / 'result.json').exists():
        return read_json(output / 'result.json')
    started = time.perf_counter()
    spec = read_json(run / 'study.json')
    trace = Trace.load(run / 'histories' / f'{parent}.npz')
    seed = seed_for(spec, int(parent.split('_')[-1]), repeat)
    model = SpatialModel(Config(**trace.config))
    base = Observer(model, ObserverConfig(**settings))
    observed = base.observations(trace, noise=noise, seed=seed)
    arrays, state_arrays, rows, failures = {'observed': observed}, {}, [], []
    estimates = {}
    for key, lateral, window in conditions(spec):
        if progress:
            progress('Estimating ' + key)
        try:
            base.config = replace(base.config, use_lateral=lateral)
            estimates[key] = infer_condition(base, trace, observed, window, spec)
        except Exception as exc:
            failures.append({'method': key, 'stage': 'inference', 'error': str(exc),
                             'traceback': traceback.format_exc()})
    try:
        estimates['replay'] = base.infer(trace, 'full', observed)
    except Exception as exc:
        failures.append({'method': 'replay', 'stage': 'inference', 'error': str(exc)})
    estimates['truth'] = Estimate(trace.checkpoint(), 0., {'privileged': True})
    for method, estimate in estimates.items():
        if progress:
            progress('Forecasting ' + method)
        state = estimate.state
        digest = hashlib.sha256(state.z.tobytes() + state.u.tobytes() +
                                np.asarray([state.d, state.v, state.t]).tobytes()).hexdigest()
        state_arrays[method + '_z'] = state.z
        state_arrays[method + '_u'] = state.u
        state_arrays[method + '_tool'] = np.asarray([state.d, state.v, state.t])
        for action_index, action in enumerate(actions):
            try:
                with np.load(run / 'truth' / f'{parent}_{action.replace(" ", "_")}.npz') as data:
                    truth = {key: data[key] for key in ('time', 'force', 'markers', 'd', 'v', 'command')}
                    truth_audit = json.loads(str(data['audit']))
                if method == 'truth':
                    forecast = truth
                    forecast_seconds = 0.
                    physical = truth_audit
                else:
                    future = model.simulate(truth['command'][1:], state=state)
                    forecast = {key: getattr(future, key) for key in ('time', 'force', 'markers', 'd', 'v')}
                    forecast_seconds = future.wall_seconds
                    physical = audit_trace(future, spec['physics_limits'])
                for channel in ('time', 'force', 'markers', 'd', 'v'):
                    arrays[f'{method}_{action_index}_{channel}'] = forecast[channel]
                error = forecast['force'] - truth['force']
                contact = truth['force'] > spec['contact_threshold_N']
                rows.append({'parent_id': parent, 'repeat': repeat, 'noise_seed': seed,
                             'noise_multiplier': noise, 'method': method, 'action': action,
                             'force_rmse_N': float(np.sqrt(np.mean(error**2))),
                             'contact_force_rmse_N': float(np.sqrt(np.mean(error[contact]**2))) if contact.any() else None,
                             'marker_rmse_m': float(np.sqrt(np.mean((forecast['markers'] - truth['markers'])**2))),
                             'inference_seconds': estimate.seconds, 'forecast_seconds': forecast_seconds,
                             'state_sha256': digest, 'physics': physical, 'inference': estimate.diagnostics})
            except Exception as exc:
                failures.append({'method': method, 'action': action, 'stage': 'forecast', 'error': str(exc),
                                 'traceback': traceback.format_exc()})
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / 'curves.npz', **arrays)
    np.savez_compressed(output / 'estimates.npz', **state_arrays)
    result = {'parent_id': parent, 'repeat': repeat, 'noise_seed': seed, 'noise_multiplier': noise,
              'observer_config': settings, 'actions': actions, 'rows': rows, 'failures': failures,
              'wall_seconds': time.perf_counter() - started}
    write_json(output / 'result.json', result)
    return result


def run_jobs(jobs, workers):
    results = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {pool.submit(evaluate_job, job): job for job in jobs}
        for future in as_completed(pending):
            result = future.result()
            results.append(result)
            print(f"{len(results)}/{len(jobs)} | {result['parent_id']} repeat {result['repeat']} | "
                  f"{result['wall_seconds']:.2f} s | {len(result['failures'])} failures", flush=True)
    return results


def calibrate(run, spec, workers):
    entries = prepare_histories(run, spec, 'calibration')
    jobs, settings = [], {}
    for candidate in spec['tuning_candidates']:
        name = candidate['name']
        settings[name] = replace(ObserverConfig(), **{k:v for k,v in candidate.items() if k != 'name'}).asdict()
        for entry in entries:
            if entry['status'] == 'completed':
                jobs.append((run, entry['id'], 0, settings[name], run/'calibration'/name/entry['id'], ['Slow press'], 1.))
    run_jobs(jobs, workers)
    scores = []
    for name, config in settings.items():
        values = [read_json(path) for path in (run/'calibration'/name).glob('*/result.json')]
        finite = [r for value in values for r in value['rows'] if r['method'] not in ('truth', 'replay')]
        failed = sum(len(value['failures']) for value in values)
        scores.append({'candidate': name, 'mean_force_rmse_N': float(np.mean([r['force_rmse_N'] for r in finite])),
                       'rows': len(finite), 'failures': failed,
                       'optimizer_nonconvergence': sum(not r['inference']['optimizer_success'] for r in finite)})
    eligible = [row for row in scores if row['failures'] == 0 and row['rows'] == len(entries)*len(conditions(spec))]
    if not eligible:
        raise RuntimeError('No complete calibration candidate; inspect retained results')
    selected = min(eligible, key=lambda row: row['mean_force_rmse_N'])['candidate']
    record = {'scores': scores, 'selected': selected, 'observer_config': settings[selected],
              'selection': spec['selection'], 'frozen_utc': datetime.now(timezone.utc).isoformat()}
    write_json(run/'calibration.json', record)
    print(json.dumps(record, indent=2), flush=True)


CONTRASTS = {
    'Lateral sensing at current time': ('basic_0.0', 'lateral_0.0'),
    'Recent 0.2 s, no lateral sensing': ('basic_0.0', 'basic_0.2'),
    'Recent 0.2 s, with lateral sensing': ('lateral_0.0', 'lateral_0.2'),
    'Recent 0.8 s, no lateral sensing': ('basic_0.0', 'basic_0.8'),
    'Recent 0.8 s, with lateral sensing': ('lateral_0.0', 'lateral_0.8'),
    'Contact vs wait update, no lateral sensing': ('basic_0.2', 'basic_contact'),
    'Contact vs wait update, with lateral sensing': ('lateral_0.2', 'lateral_contact'),
}


def summarize(run, spec):
    results = [read_json(path) for path in sorted((run/'test').glob('*/repeat_*/result.json'))]
    rows = [row for value in results for row in value['rows']]
    failures = [dict(parent_id=value['parent_id'], repeat=value['repeat'], **f)
                for value in results for f in value['failures']]
    generation = read_json(run/'test_histories.json')
    physical_failures = [dict(parent_id=e['id'], stage='physical history', **e['physics'])
                         for e in generation if e['status']=='completed' and not e['physics']['passed']]
    physical_failures += [dict(parent_id=r['parent_id'], repeat=r['repeat'], method=r['method'],
                              action=r['action'], stage='forecast', **r['physics'])
                          for r in rows if not r['physics']['passed']]
    with (run/'metrics.csv').open('w', newline='', encoding='utf-8') as stream:
        fields = ['parent_id','repeat','noise_seed','noise_multiplier','method','action','force_rmse_N',
                  'contact_force_rmse_N','marker_rmse_m','inference_seconds','forecast_seconds','state_sha256']
        writer = csv.DictWriter(stream, fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)
    means, contrasts, optimizer = [], [], []
    for method, _, _ in conditions(spec):
        fitted = [r['inference'] for r in rows if r['method']==method and r['action']==spec['actions'][0]]
        optimizer.append({'method':method,'fits':len(fitted),
            'nonconverged':sum(not r['optimizer_success'] for r in fitted),
            'unchanged_initial_coefficients':sum(np.allclose(r['basis_coefficients'],
                r['observer_config']['initial_coefficient'],atol=1e-10,rtol=0) for r in fitted),
            'median_residual_calls':float(np.median([r['solver_calls'] for r in fitted])),
            'contact_seconds_range':[min(r['observed_contact_seconds'] for r in fitted),
                                     max(r['observed_contact_seconds'] for r in fitted)]})
    rng = np.random.default_rng(spec['noise_root_seed'])
    for action in spec['actions']:
        for method in [item[0] for item in conditions(spec)] + ['replay','truth']:
            selected = [row for row in rows if row['action']==action and row['method']==method]
            means.append({'action':action, 'method':method, 'observations':len(selected),
                          'mean_force_rmse_mN':float(np.mean([r['force_rmse_N']*1e3 for r in selected])),
                          'mean_marker_rmse_um':float(np.mean([r['marker_rmse_m']*1e6 for r in selected]))})
        for label, (before, after) in CONTRASTS.items():
            paired = []
            for seed in spec['test_seeds']:
                parent = f'test_{seed}'
                lookup = {(r['repeat'],r['method']):r['force_rmse_N'] for r in rows
                          if r['action']==action and r['parent_id']==parent}
                if all((rep,m) in lookup for rep in range(spec['noise_repeats']) for m in (before,after)):
                    gain = np.mean([lookup[rep,before]-lookup[rep,after] for rep in range(spec['noise_repeats'])])*1e3
                    paired.append({'parent_id':parent, 'improvement_mN':float(gain)})
            values = np.array([r['improvement_mN'] for r in paired])
            bootstrap = rng.choice(values, (spec['bootstrap_resamples'],len(values)), replace=True).mean(axis=1)
            contrasts.append({'action':action, 'contrast':label, 'before':before, 'after':after,
                              'n_histories':len(values), 'mean_improvement_mN':float(values.mean()),
                              'ci95_mN':np.quantile(bootstrap,[.025,.975]).tolist(), 'parent_values':paired})
    summary = {'status':'exploratory completed batch', 'planned_histories':len(spec['test_seeds']),
               'completed_histories':sum(e['status']=='completed' for e in generation),
               'completed_jobs':len(results), 'expected_jobs':len(spec['test_seeds'])*spec['noise_repeats'],
               'means':means, 'contrasts':contrasts, 'failures':failures,
               'optimizer_by_method':optimizer,
               'calibration_physical_failures':[e for e in read_json(run/'calibration_histories.json')
                                                if e['status']=='completed' and not e['physics']['passed']],
               'generation_failures':[e for e in generation if e['status']!='completed'],
               'physical_failures':physical_failures,
               'optimizer_nonconvergence':sum(r['action']==spec['actions'][0] and
                   r['inference'].get('optimizer_success') is False for r in rows),
               'analysis':spec['analysis'], 'scope':spec['scope']}
    write_json(run/'summary.json',summary)
    write_json(run/'failures.json',{'generation':summary['generation_failures'],
                                  'computation':failures,'physical_limits':physical_failures,
                                  'calibration_physical_limits':summary['calibration_physical_failures'],
                                  'optimizer_nonconvergence':summary['optimizer_nonconvergence']})
    return summary


def verify_run(run, spec):
    """Check recorded information use and action reuse without rerunning fits."""
    results = [read_json(p) for p in sorted((run/'test').glob('*/repeat_*/result.json'))]
    checks, seeds, intervals = [], [], []
    observation_error = 0.
    same_states, channel_masks = True, True
    for result in results:
        parent, repeat = result['parent_id'],result['repeat']
        seeds.append(result['noise_seed'])
        trace = Trace.load(run/'histories'/f'{parent}.npz')
        expected = trace.observation + np.random.default_rng(result['noise_seed']).normal(
            size=trace.observation.shape)*NOISE_STD
        with np.load(run/'test'/parent/f'repeat_{repeat}'/'curves.npz') as data:
            observation_error = max(observation_error,float(np.max(np.abs(data['observed']-expected))))
        for method,lateral,window in conditions(spec):
            rows = [r for r in result['rows'] if r['method']==method]
            same_states &= len(rows)==len(spec['actions']) and len({r['state_sha256'] for r in rows})==1
            for row in rows:
                channel_masks &= row['inference']['fitted_channels']==([2,3,4] if lateral else [2])
            if rows:
                info = rows[0]['inference']
                intervals.append(dict(parent_id=parent,repeat=repeat,method=method,
                    update_start_s=info['update_interval_s'][0],update_end_s=info['update_interval_s'][1],
                    propagation_start_s=info['propagation_interval_s'][0],propagation_end_s=info['propagation_interval_s'][1],
                    contact_seconds=info['observed_contact_seconds'],
                    phase_seconds=info['phase_seconds'],motion_sample_count=info['motion_sample_count']))
    def check(label, passed, value):
        checks.append({'check':label,'passed':bool(passed),'value':value})
    expected_jobs = len(spec['test_seeds'])*spec['noise_repeats']
    check('Complete nominal-noise jobs',len(results)==expected_jobs,len(results))
    check('Calibration and test histories disjoint',not set(spec['calibration_seeds']) & set(spec['test_seeds']),
          {'calibration':len(spec['calibration_seeds']),'test':len(spec['test_seeds'])})
    check('Independent noise seeds',len(set(seeds))==expected_jobs,len(set(seeds)))
    check('Stored observations reproduce exactly',observation_error==0.,observation_error)
    check('Same estimate reused across actions',same_states,'SHA256 of internal fields and tool state')
    check('Recorded residual channels match masks',channel_masks,'F or F + left + right')
    check('Physical configuration unchanged',read_json(run/'physics.json')==read_json(ROOT/spec['physics']),spec['physics'])
    write_json(run/'coverage.json',intervals)
    record = {'checks':checks,'all_passed':all(c['passed'] for c in checks),
              'unit_tests':'tests/test_observer_config.py additionally mutates disabled channels and propagation-only inputs'}
    write_json(run/'verification/data_contract.json',record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare','timing','calibrate','evaluate','summarize','figures','verify'])
    parser.add_argument('--config',type=Path,default=ROOT/'configs/information_study.json')
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    spec=read_json(args.config)
    run=ROOT/spec['run']
    started=time.perf_counter()
    run.mkdir(parents=True,exist_ok=True)
    (run/'truth').mkdir(exist_ok=True)
    if (run/'study.json').exists() and spec != read_json(run/'study.json'):
        raise ValueError('Use a new run path for a changed study specification')
    if args.stage=='prepare':
        physics = read_json(ROOT/spec['physics'])
        if (run/'physics.json').exists() and physics != read_json(run/'physics.json'):
            raise ValueError('Use a new run path for changed physics')
        write_json(run/'study.json',spec)
        write_json(run/'physics.json',physics)
        write_json(run/'environment.json',environment())
        (run/'source').mkdir(exist_ok=True)
        for path in (ROOT/'src/nr2d').glob('*.py'):
            shutil.copy2(path,run/'source'/path.name)
        prepare_histories(run,spec,'calibration')
    else:
        if args.stage=='timing':
            parent=f"calibration_{spec['calibration_seeds'][0]}"
            result=evaluate_job((run,parent,0,ObserverConfig().asdict(),run/'timing',spec['actions'],1.))
            write_json(run/'cost_estimate.json',{'measured_job_seconds':result['wall_seconds'],
                       'planned_test_jobs':len(spec['test_seeds'])*spec['noise_repeats'],
                       'estimated_serial_seconds':result['wall_seconds']*len(spec['test_seeds'])*spec['noise_repeats'],
                       'workers':args.workers,'actual_test_history_count':len(spec['test_seeds']),
                       'decision':'Retain the planned 24 histories; parallelize independent jobs on CPU.'})
            print(json.dumps(read_json(run/'cost_estimate.json')),flush=True)
        elif args.stage=='calibrate':
            calibrate(run,spec,args.workers)
        elif args.stage=='evaluate':
            settings=read_json(run/'calibration.json')['observer_config']
            entries=prepare_histories(run,spec,'test')
            jobs=[(run,e['id'],rep,settings,run/'test'/e['id']/f'repeat_{rep}',spec['actions'],1.)
                  for e in entries if e['status']=='completed' for rep in range(spec['noise_repeats'])]
            run_jobs(jobs,args.workers)
            diagnostic=[(run,f'test_{seed}',0,settings,run/'noiseless'/f'test_{seed}',spec['actions'],0.)
                        for seed in spec['noiseless_diagnostic_seeds']]
            run_jobs(diagnostic,args.workers)
            summarize(run,spec)
        elif args.stage=='summarize':
            summarize(run,spec)
        elif args.stage=='figures':
            from .plotting import export_information
            export_information(run)
        elif args.stage=='verify':
            print(json.dumps(verify_run(run,spec),indent=2),flush=True)
    write_json(run/f'{args.stage}_timing.json',{'wall_seconds':time.perf_counter()-started,
               'workers':args.workers,'utc':datetime.now(timezone.utc).isoformat()})
    print(f'{args.stage} finished in {time.perf_counter()-started:.2f} s | {run}',flush=True)


if __name__=='__main__':
    main()

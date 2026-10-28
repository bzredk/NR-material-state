"""Configuration must affect inference and must not overwrite published results."""
from dataclasses import replace
import hashlib
import json

import numpy as np

from nr2d.estimators import Observer, ObserverConfig, compare_predictions
from nr2d.experiments import ROOT, comparison_directory, forecasts_for, select_pair, write_json
from nr2d.physics import Config, SpatialModel
from nr2d.protocols import protocol


def short_history():
    model = SpatialModel(Config(nx=8, ny=4, dt=.02))
    commands, phases, _ = protocol(model.c, amplitude=.0003, include_future=False)
    return model, model.simulate(commands, phases)


def test_named_preset_preserves_published_defaults():
    configured = ObserverConfig(**json.loads((ROOT / 'configs/observer.json').read_text()))
    assert configured.asdict() == ObserverConfig().asdict()


def test_requested_budget_and_window_reach_inference_and_forecast():
    model, trace = short_history()
    config = replace(ObserverConfig(), max_nfev=1, short_window_seconds=.04,
                     force_residual_scale_N=.008, regularization_weight=.03)
    forecasts, metrics = compare_predictions(model, trace, observer=Observer(model, config), noise=1.)
    fitted = metrics['Short classical']['inference']
    assert fitted['window_seconds'] == .04
    assert fitted['optimizer_nfev'] == 1
    assert fitted['observer_config'] == config.asdict()
    assert forecasts['Short classical'].metadata['comparison']['observer_config'] == config.asdict()
    assert metrics['True state']['inference']['optimization_used'] is False
    assert np.all(np.isfinite(forecasts['Short classical'].force))


def test_disabled_lateral_input_cannot_change_any_estimate():
    model, trace = short_history()
    observer = Observer(model, replace(ObserverConfig(), use_lateral=False, max_nfev=3))
    observed = observer.observations(trace, noise=1., seed=85)
    changed = observed.copy()
    changed[:, 3:] = np.nan
    for window, end in [(0., None), (.2, None), (.2, 35), ('full', None)]:
        a = observer.infer(trace, window, observed, update_end=end)
        b = observer.infer(trace, window, changed, update_end=end)
        np.testing.assert_array_equal(a.state.z, b.state.z)
        np.testing.assert_array_equal(a.state.u, b.state.u)
        assert (a.state.d, a.state.v) == (b.state.d, b.state.v)


def test_contact_update_uses_only_motion_after_update():
    from nr2d.information import contact_end
    model, trace = short_history()
    observer = Observer(model, replace(ObserverConfig(), max_nfev=2))
    observed = observer.observations(trace, noise=1., seed=91)
    end = contact_end(observed, model.c.dt, .2, .0045)
    changed = observed.copy()
    changed[end+1:, 2:] = np.nan
    a = observer.infer(trace,.2,observed,update_end=end)
    b = observer.infer(trace,.2,changed,update_end=end)
    np.testing.assert_array_equal(a.state.z,b.state.z)
    np.testing.assert_array_equal(a.state.u,b.state.u)
    assert a.diagnostics['propagation_interval_s'] == [trace.time[end],trace.time[-1]]
    # Contact selection receives the measured signal, not contact labels.
    inactive = observed.copy()
    inactive[:,2] = 0.
    import pytest
    with pytest.raises(ValueError,match='No observed contact'):
        contact_end(inactive,model.c.dt,.2,.0045)


def test_explicit_settings_do_not_replay_or_replace_legacy_cache(tmp_path):
    model, trace = short_history()
    run = tmp_path / 'run'
    trace.save(run / 'histories/a.npz')
    trace.save(run / 'histories/b.npz')
    write_json(run / 'config.json', model.c.asdict())
    write_json(run / 'manifest.json', {'histories': [
        {'id': name, 'path': f'histories/{name}.npz', 'status': 'completed', 'split': 'test'}
        for name in ('a', 'b')]})
    write_json(run / 'matching.json', select_pair({'a': trace, 'b': trace}))
    legacy = run / 'forecasts/a_slow_press_noise0'
    trace.save(legacy / 'true_state.npz')
    write_json(legacy / 'metrics.json', {'True state': {'legacy_fixture': True}})
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in legacy.iterdir()}

    config = replace(ObserverConfig(), max_nfev=1)
    _, metrics, mode = forecasts_for(run, observer_config=config)
    assert mode.startswith('RECOMPUTED')
    assert metrics['Snapshot']['inference']['observer_config'] == config.asdict()
    changed = replace(config, regularization_weight=.03)
    assert comparison_directory(run, config) != comparison_directory(run, changed)
    _, replayed, mode = forecasts_for(run)
    assert mode.startswith('REPLAY') and replayed['True state']['legacy_fixture']
    assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in legacy.iterdir()}
    output = comparison_directory(run, config)
    assert json.loads((output / 'observer_config.json').read_text()) == config.asdict()


def test_cli_sweep_and_widget_use_the_requested_settings(tmp_path, monkeypatch):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from nr2d.cli import main
    from nr2d.widgets import SweepDashboard

    model, _ = short_history()
    run = tmp_path / 'configured_run'
    write_json(run / 'config.json', model.c.asdict())
    config = replace(ObserverConfig(), max_nfev=1, sweep_windows_seconds=(0., .04),
                     short_window_seconds=.04)
    config_path = tmp_path / 'observer.json'
    write_json(config_path, config.asdict())
    monkeypatch.setattr('sys.argv', ['nr2d', 'sweep', '--run', str(run),
                                    '--observer-config', str(config_path)])
    main()
    output = comparison_directory(run, config) / 'sweeps/hold_noise0.json'
    result = json.loads(output.read_text())
    assert result['observer_config'] == config.asdict()
    assert [row['window'] for row in result['rows']] == [0., .04, 'full']
    assert result['rows'][1]['diagnostics']['optimizer_nfev'] == 1
    dashboard = SweepDashboard(run, observer_config=config)
    assert dashboard.last_error is None
    assert dashboard.progress.value == dashboard.progress.max == 3
    assert len(dashboard.fig.axes[0].lines[0].get_xdata()) == 2
    plt.close(dashboard.fig)
    dashboard.widget.close()

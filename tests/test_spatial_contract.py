"""Meaningful solver/information-boundary regressions for the research demo."""
from dataclasses import replace
import numpy as np

from nr2d.physics import Config, SpatialModel
from nr2d.protocols import protocol, future_commands
from nr2d.experiments import select_pair


def small_trace():
    model = SpatialModel(Config(nx=8, ny=4, dt=.02))
    commands, phases, _ = protocol(model.c, amplitude=.0003, include_future=False)
    return model, model.simulate(commands, phases)


def test_balance_contact_and_real_lateral_deformation():
    model, trace = small_trace()
    assert trace.force.max() > .05
    assert np.max(np.abs(trace.markers)) > 1e-6
    assert np.max(trace.diagnostics[:, :2]) < 2e-7
    assert np.max(trace.force[trace.phase == "wait"]) == 0
    assert np.all(trace.u[:, model.fixed] == 0)


def test_fork_is_deterministic_and_does_not_mutate_checkpoint():
    model, trace = small_trace()
    state = trace.checkpoint()
    saved = state.copy()
    commands, phases = future_commands(state, model.c, "Fast press", duration=.3)
    a = model.simulate(commands, phases, state=state)
    b = model.simulate(commands, phases, state=state)
    assert np.array_equal(a.force, b.force)
    assert np.array_equal(state.u, saved.u)
    assert np.array_equal(state.z, saved.z)
    assert state.t == saved.t


def test_pair_selection_is_independent_of_hidden_fields():
    _, trace = small_trace()
    other = replace(trace, z=trace.z*17, metadata={"unavailable_future": "must not be read"})
    first = select_pair({"a": trace, "b": other})
    other.z[:] = np.nan  # A test-only sentinel, never used to generate physical data.
    second = select_pair({"a": trace, "b": other})
    assert first == second
    assert first["selected"]["accepted"]


def test_classical_replay_uses_observations_not_truth_fields():
    from nr2d.estimators import Observer
    model, trace = small_trace()
    observer = Observer(model)
    a = observer.infer(trace, "full").state
    corrupted = replace(trace, z=np.full_like(trace.z, np.nan), u=np.full_like(trace.u, np.nan))
    b = observer.infer(corrupted, "full").state
    assert np.allclose(a.z, b.z)
    assert np.allclose(a.z, trace.z[-1], atol=1e-9)

"""Classical state estimates from current measurements or a motion history.

Finite windows fit an initial internal-strain field in a model-generated basis.
Full replay starts relaxed and integrates the measured tool positions. Future
predictions use the same command-driven spatial solver for every estimate.
"""
from dataclasses import asdict, dataclass
import time

import numpy as np
from scipy.optimize import least_squares

from .physics import State, SpatialModel, Trace
from .protocols import future_commands

METHODS = ["Snapshot", "Short classical", "Full classical", "True state"]
COLORS = {
    "Snapshot": "#C04A32",
    "Short classical": "#D69A20",
    "Full classical": "#167A70",
    "True state": "#253D65",
}
# Synthetic specifications, ordered as position, velocity, force, left, right.
RESOLUTION = np.array([2e-6, 5e-5, .006, 5e-6, 5e-6])
NOISE_STD = np.array([.5e-6, 1e-5, .0015, 1e-6, 1e-6])
DEFAULT_NOISE_SEED = 123


@dataclass(frozen=True)
class ObserverConfig:
    """Published pilot defaults. Scales divide residuals before least squares.

    The coefficient penalty is appended to the residual vector, so its squared
    contribution to the objective is regularization_weight**2 * ||c||**2.
    max_nfev is SciPy's evaluation cap, not the total finite-difference calls.
    """

    basis_depths_m: tuple = (.0001, .00028, .00045)
    force_residual_scale_N: float = .004
    lateral_residual_scale_m: float = 3e-6
    regularization_weight: float = .015
    initial_coefficient: float = .12
    coefficient_bounds: tuple = (0., 2.5)
    max_nfev: int = 7
    ftol: float = 1e-5
    xtol: float = 1e-5
    gtol: float = 1e-5
    diff_step: float = 1e-3
    short_window_seconds: float = .2
    sweep_windows_seconds: tuple = (0., .04, .1, .2, .4, .8)

    def asdict(self):
        # A stable JSON-compatible representation for config files and records.
        return {key: list(value) if isinstance(value, tuple) else value
                for key, value in asdict(self).items()}


@dataclass
class Estimate:
    state: State
    seconds: float
    diagnostics: dict


class Observer:
    def __init__(self, model: SpatialModel, config: ObserverConfig = ObserverConfig()):
        self.model = model
        self.config = config
        relaxed_strain = model.initial().z
        # These shapes depend on the known model, not on evaluation histories.
        self.basis = np.array([
            model.strain(model.equilibrate(relaxed_strain, depth))
            for depth in config.basis_depths_m
        ])
        self.coefficient_shape = (relaxed_strain.shape[0], len(self.basis))
        self.coefficient_count = int(np.prod(self.coefficient_shape))

    def observations(self, trace, noise=0., seed=DEFAULT_NOISE_SEED):
        rng = np.random.default_rng(seed)
        observed = trace.observation.copy()
        observed += rng.normal(size=observed.shape) * NOISE_STD * noise
        return observed

    def infer(self, trace: Trace, window, obs=None):
        started = time.perf_counter()
        model = self.model
        settings = self.config
        observed = trace.observation if obs is None else obs
        last = len(trace.time) - 1

        if window == "full":
            replay = model.simulate(
                trace.command[1:], trace.phase[1:], state=model.initial(),
                actual_positions=observed[1:, 0],
            )
            state = replay.checkpoint()
            state.d = float(observed[-1, 0])
            state.v = float(observed[-1, 1])
            return Estimate(state, time.perf_counter() - started, {
                "window": "full",
                "known_relaxed_start": True,
                "internal_truth_used": False,
                "solver_steps": last,
                "observation_use": "actual tool position drives material replay",
                "observer_config": settings.asdict(),
                "optimization_used": False,
            })

        steps = min(last, max(0, round(float(window) / model.c.dt)))
        begin = last - steps
        residual_scale = np.array([
            settings.force_residual_scale_N,
            settings.lateral_residual_scale_m,
            settings.lateral_residual_scale_m,
        ])
        residual_calls = 0

        def rollout(coefficients):
            internal_strain = np.einsum(
                "ij,jab->iab", coefficients.reshape(self.coefficient_shape), self.basis,
            )
            position = float(observed[begin, 0])
            displacement = model.equilibrate(internal_strain, position)
            state = State(displacement, internal_strain, position,
                          float(observed[begin, 1]), float(trace.time[begin]))
            if steps:
                replay = model.simulate(
                    trace.command[begin + 1:], trace.phase[begin + 1:], state=state,
                    actual_positions=observed[begin + 1:, 0],
                )
                return replay.checkpoint(), replay.observation[:, 2:]
            force = model.contact(displacement, position)[2]
            return state, np.r_[force, model.marker_values(displacement)][None, :]

        def residual(coefficients):
            nonlocal residual_calls
            residual_calls += 1
            _, predicted = rollout(coefficients)
            error = (predicted - observed[begin:, 2:]) / residual_scale
            return np.r_[error.ravel() / np.sqrt(len(error)),
                         settings.regularization_weight * coefficients]

        result = least_squares(
            residual,
            np.full(self.coefficient_count, settings.initial_coefficient),
            bounds=settings.coefficient_bounds,
            max_nfev=settings.max_nfev,
            ftol=settings.ftol,
            xtol=settings.xtol,
            gtol=settings.gtol,
            diff_step=settings.diff_step,
        )
        state, _ = rollout(result.x)
        state.d = float(observed[-1, 0])
        state.v = float(observed[-1, 1])
        return Estimate(state, time.perf_counter() - started, {
            "window_seconds": steps * model.c.dt,
            "basis_coefficients": result.x.tolist(),
            "basis_size": self.coefficient_count,
            "known_relaxed_start": False,
            "internal_truth_used": False,
            "solver_calls": residual_calls,
            "optimizer_nfev": int(result.nfev),
            "optimizer_status": int(result.status),
            "optimizer_success": bool(result.success),
            "weighted_residual": float(np.linalg.norm(result.fun)),
            "approximation": "Nonnegative initial-strain basis; complete spatial future model",
            "observer_config": settings.asdict(),
            "optimization_used": True,
        })


def compare_predictions(model, trace, action="Slow press", noise=0., observer=None,
                        seed=DEFAULT_NOISE_SEED, progress=None):
    observer = Observer(model) if observer is None else observer
    observed = observer.observations(trace, noise, seed)
    estimates = {}
    windows = (0., observer.config.short_window_seconds, "full")
    for label, window in zip(METHODS[:3], windows):
        if progress:
            progress(label)
        estimates[label] = observer.infer(trace, window, observed)
    estimates["True state"] = Estimate(trace.checkpoint(), 0., {
        "privileged": True, "scope": "same solver and future commands",
        "optimization_used": False,
    })

    # A common intervention; predictors never receive future achieved motion.
    commands, phases = future_commands(trace.checkpoint(), model.c, action)
    comparison = {
        "observer_config": observer.config.asdict(),
        "noise_multiplier": noise,
        "noise_std_SI": (NOISE_STD * noise).tolist(),
        "seed": seed,
    }
    forecasts = {
        name: model.simulate(commands, phases, state=estimate.state,
                             metadata={"method": name, "action": action,
                                       "comparison": comparison})
        for name, estimate in estimates.items()
    }
    truth = forecasts["True state"]
    metrics = {
        name: {
            "force_rmse_N": float(np.sqrt(np.mean((prediction.force - truth.force)**2))),
            "marker_rmse_m": float(np.sqrt(np.mean((prediction.markers - truth.markers)**2))),
            "inference_seconds": estimates[name].seconds,
            "inference": estimates[name].diagnostics,
            "comparison": comparison,
        }
        for name, prediction in forecasts.items()
    }
    return forecasts, metrics


def history_sweep(model, trace, noise=0., action="Slow press", observer=None, progress=None):
    observer = Observer(model) if observer is None else observer
    observed = observer.observations(trace, noise, DEFAULT_NOISE_SEED)
    commands, phases = future_commands(trace.checkpoint(), model.c, action)
    truth = model.simulate(commands, phases, state=trace.checkpoint())
    duration = trace.time[-1] - trace.time[0]
    windows = [w for w in observer.config.sweep_windows_seconds if w < duration] + ["full"]
    rows = []
    for window in windows:
        if progress:
            progress(str(window))
        estimate = observer.infer(trace, window, observed)
        prediction = model.simulate(commands, phases, state=estimate.state)
        rows.append({
            "window": window,
            "window_seconds": float(duration) if window == "full" else float(window),
            "force_rmse_N": float(np.sqrt(np.mean((prediction.force - truth.force)**2))),
            "marker_rmse_m": float(np.sqrt(np.mean((prediction.markers - truth.markers)**2))),
            "inference_seconds": estimate.seconds,
            "diagnostics": estimate.diagnostics,
        })
    return rows

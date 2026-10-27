# Configuration

Physical parameters and observer settings are separate. The Notebook and CLI use the same implementation. Environment installation is covered in [CONTAINER.md](CONTAINER.md).

## Files that control a run

| File | Controls |
| --- | --- |
| [`configs/spatial_contact.json`](../configs/spatial_contact.json) | Physical parameters read by both the notebook and `demo` / `checks` CLI commands |
| [`configs/observer.json`](../configs/observer.json) | Residual scales, regularization, basis, optimization budget and history windows |
| [`protocols.py`](../src/nr2d/protocols.py) | Loading phases and future action commands |
| [`estimators.py`](../src/nr2d/estimators.py) | `ObserverConfig`, sensor resolution, noise and inference |
| [`experiments.py`](../src/nr2d/experiments.py) | History seeds, splits, matching and result caches |

Commands below run from `2D/`, the default container terminal directory.

```sh
python -m nr2d.cli demo --config configs/spatial_contact.json
python -m nr2d.cli checks --config configs/spatial_contact.json
python -m nr2d.cli batch --run runs/2d_contact/pilot_c9dd23016896 --observer-config configs/observer.json --actions "Slow press" "Fast press" --noises 0 1
```

In the Notebook, `CONFIG_PATH` selects the physical JSON and `OBSERVER_CONFIG_PATH` selects observer settings. The default reuses the published histories and comparisons. Changing only observer settings reuses those histories and calculates new comparisons. Changing physics, or setting `RECOMPUTE_PILOT = True`, generates a new physical pilot. Batch and forecast commands use the selected run's saved physics.

## Physical parameters

Values are synthetic. JSON values use SI units.

| Group | JSON keys | Current setting | Reason |
| --- | --- | --- | --- |
| Body | `width`, `height`, `thickness` | 40 × 20 mm; 10 mm effective thickness | Plane strain with a fixed bottom and free sides |
| Mesh | `nx`, `ny` | 24 × 12 cells; 576 triangles | The refined pilot meets its force-convergence check |
| Contact | `radius`, `penalty` | 30 mm; 2e9 Pa/m | Circular, frictionless penalty contact with measured penetration |
| Material | `E_inf`, `E_fast`, `E_slow`, `nu` | 20 / 40 / 60 kPa; 0.35 | Elastic backbone plus two relaxing branches |
| Memory | `tau_fast`, `tau_slow` | 0.12 / 0.9 s | Separates fast and slow relaxation during the same history |
| Tool | `tool_mass`, `actuator_k`, `actuator_c` | 0.04 kg; 5000 N/m; 12 N s/m | Separates command, achieved motion and contact reaction |
| Integration | `dt`, `newton_tol`, `newton_max` | 0.01 s; 1e-8; 35 | 100 Hz simulated clock and Newton stopping conditions |
| Separation | `clearance` | 0.15 mm | Allows release and recontact |

The main loading amplitude is 0.45 mm. Load/hold/release/wait last 0.35 / 0.45 / 0.25 / 0.30 s. Recontact then ramps to 0.4 mm in 0.5 s, holds for 0.6 s and withdraws in 0.3 s. These protocol settings are in `protocols.py`, not the material JSON.

## Observer settings

The checked-in preset matches the published implementation. It changes how parameters are exposed and recorded, not the default method.

| Setting | Default | Meaning |
| --- | --- | --- |
| `basis_depths_m` | 0.0001, 0.00028, 0.00045 | Three elastic strain shapes for each of two internal branches |
| `force_residual_scale_N` | 0.004 | Force residual divisor |
| `lateral_residual_scale_m` | 0.000003 | Residual divisor for each lateral marker |
| `regularization_weight` | 0.015 | Multiplier on the coefficient residual; squared in the objective |
| `initial_coefficient` / `coefficient_bounds` | 0.12 / [0, 2.5] | Initial value and nonnegative fitting bounds |
| `max_nfev` | 7 | SciPy objective-evaluation cap; finite-difference residual calls are counted separately |
| `ftol`, `xtol`, `gtol` | 1e-5 each | Optimization stopping tolerances |
| `diff_step` | 1e-3 | Relative finite-difference step |
| `short_window_seconds` | 0.2 | Short-observer comparison window |
| `sweep_windows_seconds` | 0, 0.04, 0.1, 0.2, 0.4, 0.8 | Finite windows; full replay is appended |

Data residuals are divided by the square root of the number of samples before appending the coefficient penalty. This normalization is unchanged. Full replay does not use the optimizer; it starts from a known relaxed state. Inference records include the requested settings, actual rounded window length, optimizer status, `optimizer_nfev`, residual-call count and elapsed time.

For direct Python use:

```python
from nr2d.estimators import Observer, ObserverConfig, compare_predictions
from nr2d.experiments import read_json

settings = ObserverConfig(**read_json("configs/observer.json"))
observer = Observer(model, settings)
predictions, metrics = compare_predictions(model, trace, observer=observer)
```

## Observations and comparison conditions

| Channel | Matching band | Nominal Gaussian noise standard deviation |
| --- | ---: | ---: |
| Actual indentation | 2 um | 0.5 um |
| Actual velocity | 0.05 mm/s | 0.01 mm/s |
| Total normal force | 6 mN | 1.5 mN |
| Each lateral marker | 5 um | 1 um |

The widget noise selector multiplies those standard deviations. Matching uses all five channels and selects the first accepted pair by ID before looking at the future. Calibration seeds are 100–102, validation seeds 200–201, and test seeds 300–307. The pilot uses one noise realization per condition, shared between methods.

Snapshot and short-window fits share a six-coefficient strain basis and optimizer limits. Full replay additionally knows the relaxed initial state. True-state prediction receives the internal fields. Every method receives the same future command and uses the same solver.

## Storage

`2D/runs/` is on the host bind mount. Each pilot stores its physical configuration, histories and source versions. New observer comparisons go to `comparisons/observer_<key>/` inside that run. The key includes settings and numerical code hashes; each forecast also saves those settings in its trace metadata, inference diagnostics and provenance. Recompute retains earlier versions in that comparison folder and leaves the original published cache intact.

A fresh Notebook trajectory is saved under the ignored `notebook_runs/` directory. The [run index](../runs/README.md) separates scientific results from software verification. [Validation commands](../tools/README.md) cover routine checks and full physics/environment checks.

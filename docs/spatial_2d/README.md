# Spatial 2D hidden-state demonstration

A CPU FEM pilot for predicting how a loading history changes later contact response. The notebook combines a spatial trajectory, matched histories, future-action forecasts and a history-length sweep.

## Run

Open the project with **Dev Containers: Reopen in Container**, select `/opt/venv/bin/python`, and run `2D/spatial_2d_hidden_state.ipynb`.
See [container setup](CONTAINER.md) for build commands and [measured validation](CONTAINER_VALIDATION.md) for timings.

Run All solves a fresh main trajectory and replays the saved pilot checks, forecasts and sweeps. The timeline controls playback; **Run** buttons apply changed conditions, and **Recompute** generates new results.

```sh
python tools/validate_container.py
python tools/validate_container.py --full
python -m nr2d.cli demo --recompute
python -m nr2d.cli batch --actions "Slow press" "Fast press" --noises 0 1
python -m nr2d.cli sweep --excitation pulse --noise 1
python -m nr2d.cli export
```

The daily check runs dependencies, contract tests and one clean notebook. Use `--full` after physics/environment changes or before delivery to add refinement checks, callback tests and figure exports. `export --no-animation` writes SVG/PDF/300-dpi PNG without the GIF.

For presentation, hide the sidebars with **Ctrl+B** and **Ctrl+Alt+B**. Live canvases fit 1180 x 650 pixels. **Pause** holds the frame; **Reset** returns to zero.

## Implementation

| Module | Responsibility |
| --- | --- |
| `physics.py` | Triangle FEM, internal fields, contact, tool dynamics, checkpoints and traces |
| `protocols.py` | Past and future command sequences |
| `estimators.py` | Snapshot, finite-window fit, full-history replay and common forecasting |
| `checks.py` | Analytic references, physical invariants and numerical refinement |
| `experiments.py` | History generation, splits, matching, caches, failures and batch evaluation |
| `plotting.py` / `widgets.py` | Research figures, exports and notebook controls |
| `cli.py` | Command-line entry point using the same implementation |

Modules live in `src/nr2d/`. `runs/2d_contact/latest.json` identifies the current numerical pilot. Run directories contain configuration, raw fields, matching attempts, inference diagnostics, failures and source hashes. The [run index](../../runs/README.md) links the Windows and Linux validation records.

## Physical model

The body uses plane strain, a fixed bottom and traction-free sides. Quasistatic equilibrium is solved at every step, with a dynamic normal tool coordinate and frictionless circular contact.

| Quantity | Synthetic value |
| --- | --- |
| Body width / height / effective thickness | 40 / 20 / 10 mm |
| Mesh | 24 x 12 rectangles, 576 constant-strain triangles |
| Time step | 0.01 s |
| Indenter radius | 30 mm |
| Tool mass / actuator stiffness / damping | 0.04 kg / 5000 N/m / 12 N s/m |
| Equilibrium / fast / slow modulus | 20 / 40 / 60 kPa |
| Poisson ratio | 0.35 |
| Fast / slow relaxation time | 0.12 / 0.9 s |
| Contact penalty | 2e9 Pa/m |
| Main peak commanded indentation | 0.45 mm |

Each element carries two three-component internal-strain tensors. Stress combines equilibrium elasticity and two Maxwell branches; internal strains use backward Euler. The physical state includes these fields and tool position/velocity, together with fixed model context. Equilibrium determines displacement and contact. The circular gap gradient creates lateral and vertical reactions, and the penalty allows small penetration.

Observations are actual tool position, velocity, normal force and two lateral marker displacements. History inference uses measured motion; prediction uses the common command-driven tool model. Samples share a simulated clock. Each command after the first applies over the preceding integration interval.

## Comparison and data

Snapshot and finite-window models fit six nonnegative coefficients on model-generated strain shapes, sharing a basis, regularization and optimizer evaluation cap. Full-history replay also knows the relaxed start. True-state prediction uses the complete internal fields as a reference for the same future command. Inference times are reported for each method.

Matching uses all five current channels before future branching. Tolerances are 2 um position, 0.05 mm/s velocity, 6 mN force and 5 um per lateral marker. These are proximity bands; estimators retain raw values. The two markers are symmetric under centered loading, so they provide one lateral shape mode.

Nominal Gaussian noise standard deviations are 0.5 um position, 0.01 mm/s velocity, 1.5 mN force and 1 um per marker. Methods share the same realization; seed 123 is reused across parents. There is one noise realization per condition.

The pilot contains 3 calibration, 2 validation and 8 test histories, plus two validation sweep histories. Each complete history owns its future/noise branches. All 28 test pairs pass the selected matching bands; the independent test sample size is eight.

## Results and scope

- Main physical checks: 17/17. Default force error is 2.18% under mesh refinement and 0.33% under time-step refinement. The initial coarse-mesh result was 6.75% against the 5% threshold.
- One validation history reaches 5.0247 um penetration against the 5 um limit. Its original trace and a separate doubled-penalty diagnostic are retained.
- The selected pair's future force contrast persists on a finer mesh. Matching residuals still provide instantaneous information, especially through lateral shape.
- The 0.2 s observer improves mean noiseless prediction but loses to snapshot under nominal noise. Full replay is nearly exact with its known relaxed start and correct parameters.

The evidence covers a small-strain, same-material/same-geometry synthetic prediction pilot. Peak strain is about 4.7%; refinement checks cover total force and the selected pair contrast. The six-coefficient observer is approximate. Real-material calibration, sensor delay, broader transfer and decision benefit remain open. The archived E3 common-feedback action result is unchanged.

Next, tune noise weighting on calibration histories and evaluate new histories with independent noise, varied waits and parameter mismatch. Then test common-feedback decisions. A learned recursive state is worth adding if that comparison exposes a reproducible classical gap. Full 3D robot simulation precedes hardware operation.

The 2D geometry, lateral deformation, force response and planned mismatch experiments address Nadia's feedback through the hidden-state question; the solver and estimator choices are our implementation decisions.

## Legacy Windows environment

The original `.venv` remains usable:

```powershell
.venv\Scripts\python.exe tools/notebook_server.py start
.venv\Scripts\python.exe tools/notebook_server.py url
```

In VS Code, select **Existing Jupyter Server**, use the local URL, and choose **NR Spatial 2D (.venv)**. The token stays in ignored `.runtime/` files. `status` and `stop` manage the backend. If the old Windows connection hangs on Restart, stop/start the backend and reselect the kernel.

That workaround followed extension-host crashes on this Windows installation. The Linux native kernel and Restart are tested separately. Detailed historical observations remain in the [Windows frontend record](../../runs/2d_contact/pilot_c9dd23016896/frontend/windows/frontend_checks.json).

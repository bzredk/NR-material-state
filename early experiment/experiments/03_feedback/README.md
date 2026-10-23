# E3: shared feedback

The experiment is complete. Six existing checkpoints and the fitted material are frozen. No training, controller tuning, new material law or task was introduced.

Start with [闭环衔接简报.md](闭环衔接简报.md). The accepted results show transferable prediction information at the original encoding cut, but no useful additional action gain after the common observer receives release and contact feedback.

## Reproduce

Install the environment using [SETUP.md](../../../SETUP.md), then create an E3 work copy as shown in the [reproduction guide](../../REPRODUCING.md#e3--common-feedback). Run these commands inside the copy:

```sh
python analyze.py
python plot_results.py
python finalize.py
```

They recompute statistics and exports from the saved trajectories on CPU. For a full rerun, execute `bridge.py prepare`, `profile`, `actions` and `diagnostic` before the three commands above. Only `prepare` uses CUDA for frozen encoding; the later rollouts use CPU/Numba. There is no optimizer or training stage.

In PowerShell, `./run.ps1 -Stage analysis -Python python` runs the analysis sequence. Use `-Stage figures` for plots or `-Stage full` for the full rerun. The default interpreter is the active `python`; `-Python` also accepts an executable path.

Scripts write to the work copy's `raw/`, `results/` and `figures/` directories. The included input and vendor snapshots are sufficient, including for provenance checks. Original absolute source paths are historical records. Do not rerun `bootstrap.py` during ordinary reproduction: it created the initial snapshots and frozen configuration hashes.

## What was frozen

- First 64 stored round-3 test pair IDs, without outcome filtering; 128 histories.
- Seeds 11/23/47 for both history and snapshot encoders, each 3,777 parameters.
- Original 301×5 in-contact histories. Fields: measured `x [m], v [m/s], F [N], command u [m], dt [s]`; scale `[.006, .02, 8, .006, .01]`.
- State `z1,z2 [m]`, same order as both original simulators. No future controller enters the encoder.
- Held-out `(K,D)`: `(2200,45), (4800,45), (2200,110)`; waits `.1,.6,1.6 s`; force limits `3.5,5.5,8 N`.
- Common 300 ms release, then the unchanged fourth-round task. Posterior covariance is carried through the handoff.
- 1 ms RK4 truth/predictor, 100 Hz observations, 50 Hz actions. Original observer settings retained.
- Three preselected cases, analysis windows, thresholds and meaningful-gain criterion in `config.json` and `eval.json`, whose initial hashes are retained.

### Execution sequence

`prepare` → original-cut encoding → common release with causal observer → `actions` (identical predictive controller; reactive references) → `diagnostic` (common-command prediction) → `analyze` → `plot_results` → `finalize`.

The copied original controller is unchanged. `vendor/round4/control_bridge.py` differs only by an optional initial covariance argument; the exact diff and parity result are recorded. All methods receive causal measurements. True state is used only to generate trajectories and compute labels, task scores and diagnostic errors. Reactive control does not use the material estimate to select its actions.

## Files

| Path | Purpose |
|---|---|
| `inputs/`, `vendor/` | Required source snapshots, fixed material and checkpoints |
| `results/input_provenance.json` | SHA-256 of each original and snapshot |
| `results/preregistered_hashes.json` | Frozen comparison contract |
| `results/interface.json`, `profile.json`, `qa.json` | Interface, adapter parity, cost and focused checks |
| `raw/prepared.npz` | Original histories, encoded states, common prefix and handoff covariance |
| `raw/actions_*.npz` | Per-branch outcomes, quality, selected command histories |
| `raw/cases_*.npz` | All preselected full episode traces |
| `raw/diagnostic_*.npz` | Common-input states and command-conditioned forecasts |
| `results/episode_metrics.csv` | 31,104 episode rows; explicit prefix and end-to-end peaks |
| `results/summary.json` | Pair-cluster effects, condition means, timing and prediction diagnostics |
| `results/report_numbers.json` | Compact values used in the report |
| `figures/` | Six figures, each PNG + SVG + PDF; captions in `manifest.json` |
| `results/artifact_hashes.json` | Final code, config, data and figure hashes |
| `diagnostics/attempt1.zip` | Archived development run before prefix precision consistency fix |

Each action `ids` row is `[history_index, controller_index, wait_index, cap_index]`; `pair_index=history_index//2`, `member=history_index%2`. Do not treat controller/wait/cap branches or checkpoint seeds as independent histories. The main 95% intervals use 2,000 resamples of the 64 complete history pairs.

Trace columns are `[time,u,x,v,F,z1_true,z2_true,z1_est,z2_est,previous_rate,previous_predicted_peak,F_measured,x_measured,v_measured,true_hold_count,done_tick]`. `time` starts at the closed-loop handoff, after the common 0.3 s prefix. The final two fields are evaluation/termination bookkeeping, not inputs to the state encoder.

Prediction diagnostic `aligned` channels are `[force_RMSE_N, position_RMSE_mm, |kᵀ state_error|_N, state_RMSE_mm, |kᵀ correction|_N]`, on origins from −100 to +800 ms relative to first true re-contact, every10 ms. True-contact alignment is an analysis label; it is not supplied to the predictor. `forecasts` contains the next twelve 10 ms force predictions for each origin. The no-force-innovation runs retain measured-motion propagation and are diagnostic controls, not primary action methods.

### Interpretation boundaries

The fourth-round task force limit applies after the handoff, including the final release. The identical preceding preload/release may already exceed a later task cap. Both prefix and end-to-end peaks are retained; report them separately. Task completion time includes the wait and ends when the 200 ms hold is achieved, not when the final release ends.

A large common initial observer covariance makes the comparison rule identical but is not an optimal confidence model for every initializer. The report therefore describes a negative action result for this matched observer and task, not a universal bound on history-based control.

The first diagnostic attempt caught a float32/float64 command-prefix inconsistency of at most approximately `5.1e-10 m` under an exact-prefix assertion. That attempt is archived. The accepted code constructs one canonical float64 prefix and uses it in both action and prediction branches; the whole run was repeated without changing conditions, thresholds or case IDs.

# Reproduce an experiment

Install the environment in [SETUP.md](../SETUP.md) first. The commands below use that environment's `python`. Each experiment section starts at the **repository root**, with the environment active. After finishing one section, return to the root before starting another.

The saved runs are already included. Re-evaluation and training write files, so the commands make a working copy under `reproductions/`. A copy includes the data and checkpoints but excludes environments and caches. Choose a different destination for each attempt; the helper refuses to overwrite an existing folder.

## Check without rerunning

```sh
python "early experiment/tools/verify_bundle.py"
python "early experiment/tools/check_results.py"
python "early experiment/tools/replay_checkpoints.py"
```

These commands leave the archived results intact. CPU replay checks loading, shapes and finite predictions, and reports differences from the CUDA archive. CUDA replay also enforces the original E1 numerical tolerance. See [expected outputs and tests](../SETUP.md#check-the-archive-before-changing-anything).

## E1 · matched histories

### Evaluate the included checkpoints

Starting at the repository root:

```sh
python "early experiment/tools/check_environment.py" --require-cuda
python "early experiment/tools/workcopy.py" --experiment e1 --destination reproductions/e1
cd reproductions/e1
python experiment.py evaluate --output runs/round2_v1
```

The output argument is relative to the current directory and must stay inside the E1 work copy. This command evaluates the twelve saved models and updates `runs/round2_v1/summary.json`, prediction/state arrays, per-condition metrics and `figures/` inside that run directory. It does not train.

The historical E1 entry point requires CUDA even for `evaluate`. On CPU, use the bounded checkpoint replay from the previous section.

### Train a fresh run

In the same E1 working-copy directory, choose a run name that does not exist yet:

```sh
python experiment.py prepare --output runs/replication
python experiment.py train --output runs/replication
python experiment.py evaluate --output runs/replication
python numerical_audit.py --output runs/replication
```

Run each command after the preceding command finishes successfully. `prepare` generates the splits, fits material parameters on training data, records the environment and profiles updates. `train` fits all four model families with the three configured seeds. `evaluate` produces the comparisons and figures. `numerical_audit.py` checks integration refinement on training examples.

The main settings are in `config.json`; the evaluation definition is in `eval.json`. For a new study, edit the working copy before `prepare` and keep that configuration with its results. Reducing the dataset or changing the validation rule makes a different experiment.

After an interrupted training process:

```sh
python experiment.py train --resume --output runs/replication
python experiment.py evaluate --output runs/replication
```

Resume the same run name. Do not run `prepare` again merely to resume. The training code restores optimizer, scheduler and sampling state, and skips already converged models. Evaluation refuses runs that have not satisfied the recorded validation plateau rule; inspect `runs/replication/logs/*_meta.json` if it stops.

PowerShell users can also use `./run.ps1 -Python python -RunName replication` for the full sequence, or add `-Stage train -Resume`. The individual Python commands above work without changing script execution policy.

## E2 · transfer to future controllers

The reported E2 result lives in `02_transfer/v2`. The parent directory holds the earlier `transfer_v1` diagnostics. Copy the whole E2 folder because its cost summary also reads those predecessor records.

### Evaluate the included checkpoints

Starting at the repository root:

```sh
python "early experiment/tools/check_environment.py" --require-cuda
python "early experiment/tools/workcopy.py" --experiment e2 --destination reproductions/e2
cd reproductions/e2/v2
python experiment.py evaluate
python numerical_audit.py
python plot_results.py
python cases.py
python summarize_results.py
python decision_sensitivity.py
python audit_results.py
python qa_exports.py
```

The first command in `v2/` reruns prediction and action evaluation using the twelve saved models. The following commands generate the numerical audit, plots, example cases, summaries, sensitivity analysis and export checks. Let each finish before starting the next. New outputs go to `runs/transfer_v2/` and `figures/`, inside the copy.

In PowerShell, `./run_experiment.ps1 -Stage evaluate -Python python` runs the same sequence and stops if a step fails.

### Start a genuinely new training run

E2 always writes to **`v2/runs/transfer_v2`**. There is no `--output` option, and changing the configuration's name does not change this path. Existing converged checkpoints are skipped even without `--resume`.

Starting at the repository root, make another copy:

```sh
python "early experiment/tools/workcopy.py" --experiment e2 --destination reproductions/e2_new
```

Move the copied run outside `e2_new` before training. Keep the parent `e2_new/runs/transfer_v1` records in place.

Windows PowerShell, still at the repository root:

```powershell
$runPath = (Resolve-Path -LiteralPath 'reproductions/e2_new/v2/runs/transfer_v2').Path
$archivePath = Join-Path (Get-Location) 'reproductions/e2_new_saved_transfer_v2'
$workspacePath = (Resolve-Path -LiteralPath 'reproductions').Path + [IO.Path]::DirectorySeparatorChar
if (-not $runPath.StartsWith($workspacePath) -or -not $archivePath.StartsWith($workspacePath)) { throw 'Use paths inside reproductions.' }
if (Test-Path -LiteralPath $archivePath) { throw 'Choose a new archive name.' }
Move-Item -LiteralPath $runPath -Destination $archivePath
```

Linux Bash, still at the repository root:

```bash
if [ -e reproductions/e2_new_saved_transfer_v2 ]; then
  printf '%s\n' 'Choose a new archive name.'
else
  mv -- reproductions/e2_new/v2/runs/transfer_v2 reproductions/e2_new_saved_transfer_v2
fi
```

Then, on either platform:

```sh
cd reproductions/e2_new/v2
python experiment.py profile
python experiment.py prepare
python experiment.py train
python experiment.py evaluate
python numerical_audit.py
python plot_results.py
python cases.py
python summarize_results.py
python decision_sensitivity.py
python audit_results.py
python qa_exports.py
```

`profile` measures update time and GPU allocation; `prepare` generates new data from the configured seeds. Training uses the known material parameters in `fixed_material.json`. The model families, controller conditions, stopping rule and seeds are in `config.json`.

For an interrupted run, use `python experiment.py train --resume` from this same `v2/` directory, then continue with evaluation. Do not move the run directory a second time. As in E1, a run stopped at the update budget can remain unconverged; preserve that status rather than relabeling it as a completed result.

## E3 · common feedback

E3 uses frozen checkpoints from E2. It has no training stage.

### Recompute statistics and figures

Starting at the repository root:

```sh
python "early experiment/tools/workcopy.py" --experiment e3 --destination reproductions/e3
cd reproductions/e3
python analyze.py
python plot_results.py
python finalize.py
```

This route works on CPU with the installed dependencies. It reads saved arrays in `raw/` and writes `results/summary.json`, `results/episode_metrics.csv`, figures and updated export metadata in the copy. `finalize.py` checks the included snapshots; it does not require the original workstation.

For plots only, run `python plot_results.py` followed by `python finalize.py`. In PowerShell, `./run.ps1 -Stage analysis -Python python` runs the three-command sequence above; `-Stage figures` redraws plots from the existing analysis.

### Recompute encoding and trajectories

Use a separate copy if you want to retain the previous re-analysis. Starting at the repository root:

```sh
python "early experiment/tools/check_environment.py" --require-cuda
python "early experiment/tools/workcopy.py" --experiment e3 --destination reproductions/e3_new
cd reproductions/e3_new
python bridge.py prepare
python bridge.py profile
python bridge.py actions
python bridge.py diagnostic
python analyze.py
python plot_results.py
python finalize.py
```

`prepare` runs the six frozen encoders on CUDA and saves `raw/prepared.npz`. The later stages use CPU/Numba for the shared-controller rollouts and diagnostics. `actions` writes episode outcomes and selected-command records; `diagnostic` writes common-command forecasts. The two stages record progress in `results/action_progress.json` and `results/diagnostic_progress.json`.

These stages do not provide a per-episode resume option. If a stage is interrupted, rerun that stage and then the downstream analysis. Its output files may be replaced inside the working copy.

The input snapshots and vendored solver code are already included. Do not run `bootstrap.py` during ordinary reproduction: it was used to create the original snapshots and frozen configuration hashes. The PowerShell equivalent of the full sequence is `./run.ps1 -Stage full -Python python`.

## P1 · prepare a material session

The collection tools prepare files and inspect exported measurements. They do not connect to or drive a robot. The archive contains no real-material measurements; `verification/` is an interface test using synthetic records.

### Check the interface and create a blank form

Starting at the repository root:

```sh
python "early experiment/tools/workcopy.py" --experiment p1 --destination reproductions/lab
cd reproductions/lab
python verify_session.py
python session.py init --output collection/draft
```

The verification should report `status: passed`. It tests scheduling and assembly against the included fixture. `init` creates a blank `collection/draft/parameter_form.csv` and symbolic planning files. It deliberately does not supply physical amplitudes, speeds, waits or device limits.

Read [FIRST_SESSION_PLAN_EN.md](experiments/lab/FIRST_SESSION_PLAN_EN.md) for the pretest and [EXPERIMENTER_CARD_EN.md](experiments/lab/EXPERIMENTER_CARD_EN.md) for the session sequence. Fill the form's `value` and evidence columns from the apparatus calibration and pretest, keeping every `key` unchanged. The intended session has 24 core conditions and six reference anchors; the timing depends on the measured recovery time.

### Build the session after the pretest

In the lab working copy, after filling the form:

```sh
python session.py build --parameters collection/draft/parameter_form.csv --output collection/day1
```

Expect `protocol_24.csv`, `run_order_30.csv`, `motion_segments_relative.csv`, `time_budget.json` and a `data/` template. The resolved physical parameters are saved in `data/pretest_frozen.json`. Check the time budget before booking the full session. The motion-segment file is an offline plan; implement and log actual device execution through the lab's own control interface.

Complete `collection/day1/data/metadata.json` with units, signs, calibration and clock mapping. Update `episodes.csv` with actual attempt IDs and statuses, and fill controller schedules and events from the acquisition system. Retain failed attempts and retries. A blank field means the measurement or context is still missing.

### Assemble and inspect the first recordings

Put one CSV per actual attempt in `recordings/day1/`, preserving the original device files separately. The required columns are `episode_id`, `specimen_id`, `session_id`, `timestamp`, `command_position`, `actual_position`, `normal_force` and `phase`. Units and time interpretation must agree with `metadata.json`. Register each attempt in `episodes.csv`; extra clock or sensor columns are retained.

Once those files exist:

```sh
python session.py assemble --prepared collection/day1 --recordings recordings/day1 --output data/day1_batch
python first_batch.py inspect data/day1_batch --output runs/day1_inspect
python plot_intake.py runs/day1_inspect --output figures/day1_raw
```

You can inspect a partial batch. Read `runs/day1_inspect/intake_report.json` and the plots before fitting; the report distinguishes readiness for a constitutive fit from readiness for command-conditioned forecasting. If the acquisition system already exported a complete `raw.csv` dataset, use `inspect` on that dataset directly instead of `assemble`.

After inspection reports that fitting is ready, a small first fit is:

```sh
python first_batch.py fit runs/day1_inspect --output runs/day1_cost --models L2 --axes wait
```

The full configured comparison is `python first_batch.py fit runs/day1_inspect --output runs/day1_full`. Record its compute cost and inspect individual fits before drawing conclusions. All output paths must remain inside the lab working copy, and session-generation destinations must be new directories.

## Keep a record of a new run

Save the source commit, installed package versions, edited configuration, console log, seeds and resulting metrics with the working copy. The original archive is the reference for the slides; a run with changed settings should have its own name and report. No new training or material data are needed just to inspect the published progress.

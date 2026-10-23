# Early experiments

Code and results for the 12-slide progress presentation dated October 22, 2026. E1, E2 and E3 are completed simulations. P1 is the collection plan for the first real-material session.

For a first look, read [RESULTS.md](RESULTS.md) and open the [slides](presentation/NR_Progress_2026-10-22.pdf). To run the code, start with [installation](../SETUP.md), then follow [REPRODUCING.md](REPRODUCING.md).

## Where things are

| Directory under `experiments/` | What it contains |
| --- | --- |
| `pilot/` | The initial simulation: nine checkpoints, data, metrics and reports. |
| `01_history/` | E1, the matched-history experiment: twelve trained models, paired datasets, predictions and convergence records. |
| `02_transfer/v2/` | E2, the controller-transfer result used in the slides: twelve trained models and the full evaluation. |
| `02_transfer/` | The earlier `transfer_v1` run and its diagnostics. Use `v2/` for the reported E2 result. |
| `03_feedback/` | E3: six frozen E2 checkpoints, controller code, trajectories, statistics and figures. |
| `controller/` | The original physics, controller and two configuration snapshots used by E3. E3's runnable copies are already in its `vendor/` directory. |
| `lab/` | P1: scheduling and intake tools, a 24-condition protocol, six reference anchors, forms and an English execution card. |
| `acquisition/` | The earlier collection tools from which P1 copied its analysis code. |

The data and checkpoints are stored in Git, so cloning the repository downloads them with the code. Records under `lab/verification/` are synthetic interface examples; they are not laboratory measurements.

`presentation/` contains the PowerPoint and PDF. [PRESENTATION_MAP.md](PRESENTATION_MAP.md) links each slide to its source. The [workflow drawing](diagrams/workflow/README.md) includes PNG, SVG, PDF and Python source.

## Saved runs and new work

Keep the archived runs intact and use `tools/workcopy.py` before rerunning an experiment. Many original scripts write to fixed paths in their own directory. The reproduction guide shows where each one writes and how to start a fresh run.

The shorter folder names replace the original dated names; the [path map](provenance/layout_changes.json) records that change. Original source names, dates and hashes remain in `provenance/source_manifest.json`. `packaging_changes.json` records launcher and portability edits, while `public_manifest.json` checks the files in the current checkout.

Some historical reports still mention the original workstation's absolute paths. Those paths identify the old run; use the installation and reproduction guides above on a new machine. Python and PowerShell source use English. Original research notes retain their original language.

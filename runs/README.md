# Experiment records

| Record | Contents |
| --- | --- |
| [2D pilot `c9dd23016896`](2d_contact/pilot_c9dd23016896/RESULTS.md) | Raw fields, histories, future-action predictions, matching, statistics, figures, failures and source snapshots |
| [Initial physical checks](2d_contact/development/) | Coarse-mesh failure and subsequent refinement |
| [Linux container validation](container_validation/20261026_linux_cpu/) | Full checks, executed notebooks, native VS Code observations, exports and persistence test |
| [Quick workflow](container_validation/20261026_quick_workflow/validation.json) | Daily validation after simplifying the workflow |
| [Repository publication check](container_validation/20261026_repo_publish/validation.json) | Fresh kernel and callback checks after moving the notebook to `2D/` |
| [Windows frontend](2d_contact/pilot_c9dd23016896/frontend/windows/) | Original execution and native interaction records |
| [1D workcopy snapshot](workcopy_archive/20261026_cleanup/README.md) | Compact, verified recovery of earlier local reproductions |

## Pilot layout

- `config.json`, `manifest.json`, `source/`, `environment/`: configuration, complete-history splits, implementation snapshot and dependencies.
- `main.npz`, `histories/`: spatial trajectories and internal fields.
- `matching.json`, `forecasts/`, `sweeps/`: current-observation matching and subsequent comparisons.
- `checks.json`, `verification/`, `pair_refinement/`, `physical_failures.json`: numerical checks, raw refinement solves and failed criteria.
- `batch.json`, `summary.json`, `figures/`: all evaluated conditions and exports with provenance.

New notebook sessions write a fresh main trajectory to `notebook_runs/`. These repeated interactive sessions stay on the local bind mount and are ignored by Git. The published `main.npz`, complete pilot data and container validation remain available in this repository. Standalone notebook/callback checks write to ignored `runs/notebook_validation/`; named release validation records are kept in `container_validation/`.

Historical records retain the paths and hashes observed at execution time. The main notebook moved from `output/jupyter-notebook/` to `2D/` during repository organization; historical snapshots were not rewritten.

# Object State Inference

Estimating hidden object states from interaction history.

We study what current measurements reveal, what history adds, and whether the estimate helps a robot act.

## Repository

| Directory | Contents |
| --- | --- |
| [2D/](2D/README.md) | Current spatial experiments: Notebook, setup, results, design and related papers |
| [1D/](1D/README.md) | Earlier contact experiments, figures and reproduction |
| [research/](research/README.md) | State formulation, detailed literature audits and future protocols |
| [research/presentations/](research/presentations/README.md) | Research reports, PDFs and speaking notes |

## Results so far

### Spatial 2D

The 24-history comparison finds that current lateral shape improves prediction, and recovery/contact history adds further information. The same estimates are reused for Slow press and Fast press. [Results and figures](2D/README.md#results).

[Run the experiment](2D/README.md#run) · [Related papers](2D/README.md#related-reading) · [Report 10.2](research/presentations/10.2/README.md)

### Earlier 1D

| Experiment | Recorded result |
| --- | --- |
| History dependence | History improves prediction over a snapshot. The correct-model classical estimator is more accurate; a 0.2 s observer nearly matches the history encoder. |
| Controller transfer | One state estimate can predict responses under the tested future controllers. |
| Shared feedback | History-based initialization adds no useful action benefit with the common observer and controller. |

[1D measurements and conditions](1D/RESULTS.md) · [Code and reproduction](1D/README.md)

These are synthetic-material simulations. The 2D common-feedback control comparison and 3D robot manipulation remain planned.

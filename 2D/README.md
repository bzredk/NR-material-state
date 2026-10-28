# Spatial contact and hidden state

A circular indenter loads a viscoelastic body, releases it and makes contact again. The current pilot compares state estimates from instantaneous measurements, a short observation window and full loading history.

## Sensor channels and contact history

The [new comparison](runs/information/channels_contact_20261026/RESULTS.md) uses 24 independent histories and three noise draws per history. For Slow press, current lateral shape reduces mean force error from 11.50 to 2.20 mN; recent lateral history reduces it to 1.29 mN over 0.2 s and 0.23 mN over 0.8 s. The same estimates also predict Fast press.

![History duration, contact data and prediction error](runs/information/channels_contact_20261026/figures/02_window_and_contact.png)

Waiting contains useful recovery information when lateral sensing is enabled. Without it, earlier contact plus motion propagation is much more informative. [Section 5 of the Notebook](notebooks/spatial_2d_hidden_state.ipynb) provides sensor, window and future-action controls. The original pilot below is retained; its noisy-short-window loss does not generalize to the new batch.

## Pilot results

Start with [the recorded pilot](runs/2d_contact/pilot_c9dd23016896/RESULTS.md). It contains eight independent test histories, the force-error comparison and the retained penetration-limit failure.

![Recorded 2D histories, endpoint measurements and response to the same command](docs/figures/hidden_state_pair.png)

The recorded pair has identical endpoint tool position, velocity and contact force. The lateral-marker residual is 2.18 um against a 5 um matching tolerance. The same slow-press command produces a maximum force difference of 9.65 mN in simulation. Geometry is displayed at 1:1 deformation scale; the response axes include zero.

The pair was selected from current measurements before computing the future response. All five current channels are shown. The remaining lateral difference can still provide instantaneous information; this pair alone does not establish that history is necessary. [Source data](docs/figures/hidden_state_pair.csv) · [Conditions and provenance](docs/figures/hidden_state_pair.json) · [SVG](docs/figures/hidden_state_pair.svg) · [PDF](docs/figures/hidden_state_pair.pdf).

Short history helps in noiseless prediction and degrades under nominal noise. Full replay benefits from known parameters and a relaxed initial state. This pilot does not compare controllers.

## Run

Open [the notebook](notebooks/spatial_2d_hidden_state.ipynb) using the [Docker / VS Code instructions](docs/CONTAINER.md). Run All computes one fresh spatial trajectory and replays recorded comparisons, including the new study. The slider controls playback; Run and Recompute buttons control calculation.

[Observer and physical settings](docs/CONFIGURATION.md) are shared with the CLI. New observer comparisons are stored separately from the published results.

## Code and documentation

| Location | Contents |
| --- | --- |
| [src/nr2d/](src/nr2d/) | Solver, estimators, experiment functions and plots |
| [configs/](configs/) | Physical parameters and observer settings |
| [tests/](tests/) | Physical, information-use and configuration regressions |
| [tools/](tools/README.md) | Execution, figure export and validation commands |
| [docs/README.md](docs/README.md) | Physical model, observations and estimator assumptions |
| [docs/DESIGN.md](docs/DESIGN.md) | Experiment rationale and original process diagram |
| [runs/](runs/README.md) | Scientific evidence first; development records in a separate index |

Environment installation and kernel selection are documented in [CONTAINER.md](docs/CONTAINER.md); parameter definitions are in [CONFIGURATION.md](docs/CONFIGURATION.md).

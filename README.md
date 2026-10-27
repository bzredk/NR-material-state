# NR material state

Experiments on object state estimation from contact history. The current 2D model has fast and slow internal relaxation. We compare estimates based on current measurements, short observation windows and full loading histories.

[2D notebook](2D/notebooks/spatial_2d_hidden_state.ipynb) · [Docker setup](2D/docs/CONTAINER.md) · [Parameters](2D/docs/CONFIGURATION.md) · [Experiment design](2D/docs/DESIGN.md)

Open the repository in VS Code, choose **Dev Containers: Reopen in Container**, then open the notebook. Select the container's **Python 3.11.9** and **Run All**.

![2D experiment: loading histories, state estimation and future response](2D/docs/figures/experiment_flow.svg)

## Results so far

### Spatial 2D

In the eight-history 2D pilot, a 0.2 s observer reduced force-prediction error for slow and fast presses without noise. Under the nominal noise setting, the instantaneous fit was better. Full replay was accurate with the correct model and a known relaxed start. [Results and paired histories](2D/README.md#pilot-results).

### Earlier 1D

| Experiment | Recorded result |
| --- | --- |
| History dependence | History improves prediction over a snapshot. The correct-model classical estimator is more accurate; a 0.2 s observer nearly matches the history encoder. |
| Controller transfer | One state estimate can predict responses under the tested future controllers. |
| Shared feedback | History-based initialization adds no useful action benefit with the common observer and controller. |

[1D measurements and conditions](1D/RESULTS.md) · [Code and reproduction](1D/README.md)

These are synthetic-material simulations. The 2D action comparison and 3D robot manipulation remain planned.

## Repository

```text
1D/                 Earlier experiments and their evidence
2D/
  notebooks/        Interactive demonstration
  configs/          Physical and observer settings
  environment/      Docker image and pinned dependencies
  src/              Solver, estimators and plotting
  tests/            Physical and information checks
  tools/            Execution and validation
  docs/             Setup, design and configuration
  runs/             Raw data, figures and run records
research/           Research notes and future protocols
```

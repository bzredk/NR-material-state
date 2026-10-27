# Model and comparison

## Physical model

The body uses small-strain plane strain, a fixed bottom and traction-free sides. Quasistatic equilibrium is solved at every step, with a dynamic normal tool coordinate and frictionless circular contact. The numerical parameters are in [CONFIGURATION.md](CONFIGURATION.md#physical-parameters).

Each element carries two three-component internal-strain tensors. Stress combines equilibrium elasticity and two Maxwell branches; internal strains use backward Euler. The state contains these fields and tool position/velocity, together with fixed material and geometry. Equilibrium determines displacement and contact. The circular gap gradient produces lateral and vertical reactions; the penalty contact permits small penetration.

## Observations and inference

The five observed channels are actual tool position, velocity, normal force and two lateral marker displacements. Samples share a simulated clock. Each command after the first applies over the preceding integration interval. Inference uses measured motion; future prediction uses the command-driven tool model.

Snapshot and finite-window fits estimate nonnegative coefficients on model-generated initial-strain shapes. Position drives the replay; force and lateral displacement form the residual. The residual is divided by its channel scales and by the square root of the number of samples. A coefficient penalty is appended before least squares. [The observer preset](../configs/observer.json) exposes those scales, penalty, basis depths, optimizer limits and history windows.

Full-history replay starts from known relaxed internal strain. It does not fit coefficients. True-state prediction receives the complete internal fields as a reference for the same future command. Neither is an absolute upper bound over all possible controllers. Optimization counts and actual inference time are recorded; a shared evaluation cap does not imply equal solver work across window lengths.

Matching uses all five current channels before future branching. The limits are proximity bands: estimators retain the raw values. Both markers are symmetric under centered loading and provide one lateral shape mode. Noise is shared across methods, with one realization per condition and seed 123 reused across parents. Sensor limits and noise levels are synthetic; [their values are recorded here](CONFIGURATION.md#observations-and-comparison-conditions).

## Data

The pilot contains 3 calibration, 2 validation and 8 test histories, plus two validation histories for window sweeps. Each complete history owns its future/noise branches. All 28 test pairs pass the chosen matching bands; the independent test count remains eight.

[The pilot manifest](../runs/2d_contact/pilot_c9dd23016896/manifest.json) records those splits and [the results](../runs/2d_contact/pilot_c9dd23016896/RESULTS.md) report the method comparison. New code and observer settings write separate comparison records. Published source snapshots retain the implementation that produced each earlier result.

## Results and scope

The evidence covers a small-strain, same-material, same-geometry synthetic prediction study. Peak strain is about 4.7%; refinement checks cover total force and the selected pair contrast. Matching residuals leave instantaneous information, especially through lateral shape. The six-coefficient observer is approximate.

The [result report](../runs/2d_contact/pilot_c9dd23016896/RESULTS.md) includes the failed penetration criterion; the [physical audit](../runs/2d_contact/pilot_c9dd23016896/physical_failures.json) preserves the original and diagnostic runs. Real-material calibration, sensor delay, broader transfer and decision benefit remain open. The [next comparison](DESIGN.md#next-comparison) starts with noise weighting and independent histories.

The 2D geometry, lateral deformation and force response address Nadia's feedback through the hidden-state question. Solver and estimator choices are implementation decisions made in this project.

## Implementation

| Module | Responsibility |
| --- | --- |
| [physics.py](../src/nr2d/physics.py) | FEM, internal fields, contact, tool dynamics and saved traces |
| [protocols.py](../src/nr2d/protocols.py) | Loading histories and future commands |
| [estimators.py](../src/nr2d/estimators.py) | Observer configuration, inference and shared prediction |
| [experiments.py](../src/nr2d/experiments.py) | Data splits, matching, comparisons and run records |
| [checks.py](../src/nr2d/checks.py) | Physical references and refinement checks |
| [plotting.py](../src/nr2d/plotting.py) / [widgets.py](../src/nr2d/widgets.py) | Figures and native Notebook interaction |
| [cli.py](../src/nr2d/cli.py) | The same implementation from the command line |

[Setup](CONTAINER.md) · [Parameters](CONFIGURATION.md) · [Experiment design](DESIGN.md) · [Evidence index](../runs/README.md)

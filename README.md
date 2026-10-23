# NR · material memory

Press a soft material, release it, then press it again. The second force response can depend on the first loading history, even when the current position and force look the same.

This project studies how much of that history a robot needs to keep. A small recurrent encoder estimates two internal material variables. A fixed physics model then uses that estimate to predict the response to the next command.

The experiments so far use a one-dimensional contact simulator. History improves prediction in the matched-history and controller-transfer tests. A classical observer is also competitive. When all methods receive the same feedback during execution, the learned initialization adds no useful action benefit in the tested task. That result is why the next experiment focuses on contact geometry, lateral deformation and response mismatch.

## Run it

Start with the [setup guide](SETUP.md), or [中文安装与运行说明](docs/SETUP.zh-CN.md). It covers Windows PowerShell and Linux, CPU and CUDA installation, expected outputs, and common errors.

Once the environment is installed, these commands check the saved results from the repository root:

```sh
python "early experiment/tools/check_environment.py"
python "early experiment/tools/verify_bundle.py"
python "early experiment/tools/check_results.py"
python "early experiment/tools/replay_checkpoints.py"
```

The checks work on CPU. Full E1/E2 runs and the frozen-encoder preparation in E3 require CUDA. The [reproduction guide](early%20experiment/REPRODUCING.md) gives the commands for each experiment, including fresh runs and interrupted training.

## Experiments

The archive contains the code, synthetic data, trained weights, logs and figures used in the [October 22, 2026 progress slides](early%20experiment/presentation/NR_Progress_2026-10-22.pdf) ([PowerPoint](early%20experiment/presentation/NR_Progress_2026-10-22.pptx)).

| Folder | Experiment |
| --- | --- |
| [`01_history`](early%20experiment/experiments/01_history) | E1: different histories, matched current observations, identical future command |
| [`02_transfer/v2`](early%20experiment/experiments/02_transfer/v2) | E2: reuse one state estimate under different future controllers |
| [`03_feedback`](early%20experiment/experiments/03_feedback) | E3: frozen estimates with a common observer and controller |
| [`lab`](early%20experiment/experiments/lab) | P1: first material-collection protocol and data intake; measurements are still pending |

The earlier pilot and supporting snapshots are listed in the [archive guide](early%20experiment/README.md). Read [results and interpretation](early%20experiment/RESULTS.md) for the numbers, or the [slide map](early%20experiment/PRESENTATION_MAP.md) to find a figure's source.

## How the estimate is used

![Measured history, material-state estimate, candidate predictions and action selection](early%20experiment/diagrams/workflow/interaction_history_state_flow.png)

The figure shows one decision: measured history produces a state estimate, candidate commands are rolled out, and a shared selector chooses an action. The [drawing source and vector exports](early%20experiment/diagrams/workflow) are included.

The [2D contact plan](plans/2d_contact/README.md) is the next study. It has not been implemented yet. The two internal variables in the current simulator describe material memory along one motion axis; they are not two spatial dimensions.

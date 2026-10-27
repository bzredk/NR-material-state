# Results

These are the saved simulation results behind the October 22 slides. The main finding is that history helps predict the next contact, but that gain did not produce a useful action advantage once all methods received the same feedback.

## history dependence: the current reading can miss material memory

Two different loading histories end at the same measured position, velocity, force and command. Both then receive the same future command. The history and snapshot encoders have the same capacity and use the same fixed material model.

On the held-out waiting interval:

| Method | Paired-effect NRMSE | Force RMSE (N) |
| --- | ---: | ---: |
| History encoder | 0.02282 | 0.003680 |
| Snapshot encoder | 1.00000 | 0.052179 |
| Classical estimator, correct model family | — | 0.000234 |
| Local observer, last 0.2 s | — | 0.003695 |

The history encoder recovers the difference between the two responses. The classical estimator does better still, and the short-window observer nearly matches the history encoder. This experiment supports using history; it does not establish a need for neural estimation.

The waiting interval is inside the training minimum and maximum, so this is interpolation. Complete history pairs are the statistical units. Values come from the `*/test_wait` entries in [history dependence summary.json](experiments/history_dependence/runs/round2_v1/summary.json).

## controller transfer: one estimate can be reused across future controllers

The encoder reads three seconds of interaction under a fixed controller. Each test history is encoded once. Future controller gains enter the dynamics rollout separately, allowing the same estimate to be reused under several controls.

Held-out force RMSE is approximately 0.0038 N for history, 0.0350 N for snapshot, 0.00048 N for classical integration and 0.00313 N for the local observer. These are the `transfer_v2` results; the [summary](experiments/controller_transfer/v2/runs/transfer_v2/summary.json) contains the individual seeds and conditions.

The conditional GRU comparison also changes the material-evolution model and uses a different parameter count. It therefore cannot isolate the effect of the state encoder alone. Action comparisons also need their information and action interfaces kept in view: the reactive controller has online feedback and a different action space, while the oracle has privileged information.

## shared feedback: shared feedback removes the useful action gain

Six frozen controller transfer checkpoints initialize the same observer and controller. The history-versus-snapshot gain in safe success is **0 percentage points**, with an archived 95% interval of **[0, 0]**. Completion-cost gain is approximately **−0.00000289 s**, below the predeclared useful-effect threshold. The `meaningful` flag in the [summary](experiments/shared_feedback/results/summary.json) is false.

The estimates differ at the original prediction cut. Common release and contact measurements then reduce that difference quickly. For this task and observer, better initialization did not add a useful action benefit.

## What remains to be tested

The RME-inspired estimator, literature-based LSTM and physics-augmented material-model adaptations mentioned in the slides are planned comparisons. They are not implemented baselines in these runs. The `lab/` folder contains a collection protocol and synthetic interface checks; real-material measurements are pending.

The [spatial 2D pilot](../2D/README.md#pilot-results) now includes lateral deformation and compares state estimates using current measurements and history. Material-response mismatch and an action comparison under common feedback remain planned; the [protocol](../research/2d_contact/README.md) describes those comparisons and stopping criteria.

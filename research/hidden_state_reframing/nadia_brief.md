# Next discussion with Nadia: what is known, what must be tested

Date: 2026-10-25. Research topic: **inference and representation of hidden object state**. Recoverable contact material is the present carrier, not the definition of the research area.

This brief uses archived synthetic results and a proposed diagnostic framework. No new material, spatial 2D, articulated 3D, or physical robot experiment has been completed in this reframing. The three figures below are generated from archived data or explicitly labeled schematics; they are not new experimental results.

## Meeting objective

Agree on one credible object-tool operation, its decision and sensing requirements, and the next falsifiable test. The central question is whether a compact, recursively updated object representation preserves information needed for relevant future interactions, and when that information changes action before ordinary feedback makes it redundant.

Do not choose a network first. Retain the classical solution if it already captures the useful information. A new inference method needs a demonstrated failure of strong existing approaches under matched information and execution conditions.

## Figure 1 — A present observation can hide different internal composition

![Archived synthetic example of hidden-state aliasing](D:/capp/NR/NR-material-state/plans/hidden_state_reframing/figures/01_state_aliasing.png)

**Caption.** Archived SRC-history dependence, prespecified `test_wait` pair index 0; no selection for unusually large future response. Physically replayed command histories reach matched current position, velocity, total force and command, while the two internal dashpot states differ. The same subsequent command produces different force response. True internal states and their decomposition are simulator-only evaluation information. Any accompanying mechanical diagram is an explanatory schematic of the implemented model, not a photograph or independently identified material law.

The full state `(x,v,z1,z2)` is already Markov under known parameters and the command/controller schedule. In contact, equal total force fixes `k1*z1+k2*z2`, but does not fix the branch split. With distinct time constants, `delta_F_dot = (k1/tau1)*delta_z1 + (k2/tau2)*delta_z2` can be nonzero although the current weighted sum difference is zero.

**Say:** This demonstrates omitted dynamic information in the declared observation model. **Do not say:** Real materials have been identified, the physical system is non-Markovian, or the learned representation is uniquely minimal.

**Construction caveat:** The archived generator uses a simulator-state Jacobian to choose an aliasing direction and couples endpoint sensor noise to make the two snapshots identical. Histories themselves are physically replayed. This is a privileged mechanism-isolation experiment; the next benchmark must also test independent sensor noise, resolution-based matching, and naturally sampled histories.

Source: [figure_data.json](figure_data.json), [existing_evidence.md](existing_evidence.md), and `1D/experiments/history_dependence/runs/round2_v1/data/test_wait.npz`.

## Figure 2 — Prediction improvement does not yet establish method or action necessity

![Archived prediction, observer and action evidence](D:/capp/NR/NR-material-state/plans/hidden_state_reframing/figures/02_existing_evidence.png)

**Caption.** Empirical archived synthetic evidence. history dependence force errors use the stored test-wait summaries, with complete history pairs as the sampling units. shared feedback state-error points show seed 11 before and after the common 0.3 s release; they are not an across-seed confidence interval. Task-window and prefix-inclusive outcomes have different accounting scopes and must be shown separately. Any confidence intervals reproduced from the archive retain their original assumptions; a degenerate binary bootstrap interval is not a proof of population equivalence.

| Existing observation | Supported conclusion | Missing distinction |
| --- | --- | --- |
| history dependence correct-family full-history classic RMSE about 0.000234 N; learned history about 0.003680 N | The known calibrated mechanism is a stronger explanation than neural necessity in this setup | Whether a realistic information/model condition defeats that observer |
| history dependence 0.2 s contact observer about 0.003695 N | Long history is not shown necessary in this regime | Practical window requirements across noise, contact availability and time scales |
| controller transfer one estimate reused across future gains | Limited action/controller-conditioned transfer is supported | Learned recursive filtering and broader state sufficiency remain untested |
| shared feedback initialization advantages disappear under common processing; no useful action gain | Better initial prediction is insufficient for useful control in this implementation | Feedback recovery versus covariance-induced overwrite versus task saturation |

In shared feedback, seed-11 classical state error changes from 0.000897 mm to 0.025150 mm; history from 0.014404 mm to 0.025152 mm; snapshot from 0.165452 mm to 0.025119 mm. Thus the observer improves the poor initializer while degrading more accurate ones. Similar estimates alone are not evidence of improved knowledge.

All predictive methods achieve 100% post-handoff task-window success, but prefix-inclusive success is 84.8958%: 522 of 3,456 dependent branches per method already exceed their later assigned cap in the prefix. History-minus-snapshot completion-cost gain is approximately `-2.89e-6 s`, with no meaningful safe-success improvement. The independent units are 64 history pairs, not thousands of branches.

The archived shared feedback action batch contains no true-state controller reference. Consequently it does not determine the available state-information benefit for even its fixed action/controller interface, much less for all possible policies.

## Figure 3 — Decide which bottleneck exists before expanding the method

![Proposed diagnostic decision framework](D:/capp/NR/NR-material-state/plans/hidden_state_reframing/figures/03_decision_gate.png)

**Caption.** Proposed schematic, not measured data. The map distinguishes response relevance, recoverability, recursive/predictive adequacy, feedback timing, and task utility. No region prevalence, threshold, or effect size has been measured by drawing this figure. “True-state reference” always means the same tested predictor/controller/action library and horizon; it is not an absolute optimal-control upper bound.

| Diagnostic case | Needed observation | Decision |
| --- | --- | --- |
| State affects response, task does not need it | X01 response difference; no useful state-reference action advantage after checking search/metric adequacy | Narrow the action claim or justify a different operation |
| State useful, sensing/excitation insufficient | Fixed-interface state-reference benefit; unresolved uncertainty even with adequate model-based inference | Add a feasible probe/sensor or retain a belief; do not demand impossible point recovery |
| History informative, feedback resolves it in time | Predecision forecast benefit; relevant uncertainty genuinely shrinks before the consequential choice | Report the feedback-substitution boundary and retain simple feedback |
| State useful and recoverable, inference deficient | Remaining decision benefit; available histories contain information that the current method loses | Target that specific inference or recursive-update deficiency |

The evidence chain is X01 relevance, X02 history/excitation, X03 residual older-history value, X04 recursive consistency, X05 cross-action reuse, X06 decision utility, and X07 explicitly scoped transfer. A lower-level success cannot stand in for a higher-level result. Two equally wrong predictors can agree recursively; both must also predict held-out outcomes adequately.

## What we can responsibly conclude now

1. The synthetic carrier exhibits observation aliasing with physically replayed histories.
2. Current learning infers one scalar split within a prescribed two-state law; general hidden-state discovery has not been demonstrated.
3. Correct-model classical estimation and short windows are essential strong baselines, not obstacles to remove.
4. Cross-controller reuse is supported within the tested synthetic family; general sufficiency and learned recursive updates are open.
5. shared feedback is a meaningful negative result for its matched implementation, with observer and task-ceiling qualifications. It does not reject the broader topic.
6. Generic history encoding, latent dynamics, belief updates and Markovization are established ideas. Any contribution must specify an unresolved information/inference problem or a useful, reproducible insight about action-relevant sufficiency.

The current evidence is conditional on one synthetic material law and history-generation distribution. There is no calibrated real specimen, verified spatial 2D result, complete 3D robot result, cross-mechanism result, unique-state theorem, causal-discovery result, or universal safety certificate.

## Three precise questions Nadia can help resolve

These build on the already established resource status: lab equipment can be requested, while no specimen, loading fixture or real-material measurements currently exist. They do not ask the user to repeat an equipment inventory.

| ID | Question for Nadia | Why her answer changes the study | Smallest follow-up action |
| --- | --- | --- | --- |
| NQ1 | Which single object-tool operation in the lab has a genuine force/deformation constraint and a consequential choice that may occur before feedback resolves state: what is that choice, failure consequence, and justified cycle-time requirement? | Determines whether hidden-state information could be useful without an artificial deadline or weakened feedback | Write a one-page operation specification and inspect fixed-interface true-state headroom on a validation-only feasibility set |
| NQ2 | For that operation, which supported arm/tool/force-sensing configuration should we request, who owns its maintained control stack, and which command/read-back/timestamp interface is actually authorized and supportable? | Public equipment ownership does not determine deployed control modes, synchronization, latency or force access | Arrange a short interface qualification session recording commanded and achieved motion, force, device clocks and end-to-end delay |
| NQ3 | What physically credible departure from the current known, relaxed-start two-mode model should be tested first, and what independent calibration or intervention would distinguish it from parameter error or sensor bias? | Identifies a justified inference difficulty rather than adding nonlinearity or mismatch only to defeat a classical baseline | Obtain one recoverable specimen/fixture and run a small load-hold-release/recontact calibration with side observation, comparing simpler laws before adding complexity |

The intended output of the discussion is one operation, one resource acquisition/interface path, and one independently testable departure from the current idealized information condition. A second task or carrier follows only after the first chain is informative.

## Compact statistical-fallacy review

| # | Fallacy to avoid | Required correction |
| --- | --- | --- |
| 1 | Frames, windows or future branches are independent trials | Group by parent history/physical realization; cluster further by reused specimen |
| 2 | Training seeds multiply the number of physical samples | Report seed variation within the independent experimental units |
| 3 | history dependence test-ID and test-wait are separate independent histories | They reuse the same histories; treat waits as dependent branches |
| 4 | Shared endpoint noise represents ordinary sensing | Label it a controlled ablation; use independent noise and calibrated matching in the new main study |
| 5 | Select pairs with the largest future effect or oracle disagreement | Freeze generation/matching without inspecting future outcomes; report acceptance and all retained cases |
| 6 | Tune thresholds, sample size or the task on the final test | Separate calibration, pilot, validation and final test; revise prospectively |
| 7 | Lower force RMSE proves a sufficient state or better decisions | Test residual history, recursive adequacy, action ranking and realized utility separately |
| 8 | A nonsignificant result or `[0,0]` bootstrap proves equality | Report effect intervals, discordance and appropriate bounds; equivalence requires a meaningful margin |
| 9 | A true-state controller is globally optimal | Keep its predictor, search, library, horizon and utility restrictions explicit |
| 10 | Post-handoff success is whole-operation safety | Count preload, probe, release, approach, task and retreat; report every violation and failure |
| 11 | Many exploratory contrasts or only successful runs support a confirmatory claim | Preregister the primary contrast, adjust declared comparison families, and retain failed seeds/solver errors |

Source and implementation details: [existing_evidence.md](existing_evidence.md), [formalization.md](formalization.md), [frameworks.md](frameworks.md), and [minimal_experiment.md](minimal_experiment.md).

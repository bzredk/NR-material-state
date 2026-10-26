# Minimal complete evidence chain and execution contract

## Material passport

- Mode: evidence-based design with analysis of archived results; no new experiment executed.
- Version/date: 0.1 / 2026-10-25.
- Research chain: C01-C05 first; C06 only after earlier evidence supports extension.
- Existing inputs: SRC-E1/E2/E3, SRC-AUDIO, SRC-WEB, P01/P02/P03/P04/P16, T01-T04.
- New data: D1/D2/D3 are PROPOSED. The user confirms that no specimen, loading fixture or real-material measurements currently exist. Lab equipment is requestable; deployed interfaces remain unmeasured.
- Primary deliverable: a discriminating evidence package, not a large architecture leaderboard.

## 1. Hypothesis and first task

**H1, physical/information claim:** At matched deployable current observations, physically realizable histories can carry information about future object response that a current-only model lacks, and a compact recursive representation can preserve that information across declared future commands.

**H2, separate action claim:** In at least one prospectively chosen credible task regime, that information changes the choice among feasible actions and improves task utility before common feedback supplies equivalent relevant information. H1 may hold while H2 fails.

Use one primary operation: a robot with a rigid rounded tool approaches a recoverable specimen in a fixture, recontacts after a recorded loading/recovery history, reaches and holds a target compression while respecting a force/deformation envelope, then withdraws. Include joint-limited retreat/reposition and approach in the 3D version. This is a scoped manipulation primitive, not evidence of general dexterous skill. Its practical cycle time and constraints require a justified operating specification; do not invent an urgent deadline solely to make history help.

Start with known two-mode physics as an instrumented diagnostic. The new mechanism evidence must use a spatial 2D mesh and visible lateral response. A 1D rerun may check software or explain E3, but cannot be relabeled the required spatial stage. The first 3D study has one arm/tool/task; grasp–transport or a second carrier is deferred until there is a useful state-information effect and appropriate sensing.

## 2. Data and information contract

For every sample record `episode_id`, `parent_history_id`, `object_instance_id`, `material_batch_or_model_id`, `task_id`, `phase`, units/frames, observation acquisition and delivery times, issued command time/value, execution/read-back time/value, actual robot/tool motion, force, visible shape/markers, validity flags, controller mode/gains, and sensor/filter configuration. Preserve original device timestamps and clock mapping uncertainty.

Simulator-only channels include full material/internal fields, true parameters, exact unoccluded geometry and true contact forces. Store them separately with access roles `evaluator`, `state_reference`, or `privileged_training`. The main learner gets future deployable observations as prediction targets, not internal-field labels. A hidden-state-supervised variant is a separate privileged comparison. Record all RNN hidden/cell states, observer covariance and filters; an emitted low-dimensional code is not the whole memory if another buffer is retained.

During prediction, supply future **commands and controller context**. Actual future indentation, tool displacement, force or images are targets, not inputs. Material-point models with prescribed strain input can be used for constitutive validation but do not alone implement command-conditioned robot prediction. Past actual motion is available to a filter only after its measurement arrives.

Calibration data identify material/actuator/sensor models before representation comparisons. A known relaxed-start flag is shared with every estimator in that stratum; otherwise all methods face an explicitly unknown initial state. Contact status is either inferred from shared channels or supplied as a declared common observation. Do not let only the classical method know contact truth, or deprive it of a legitimate observed contact interval.

### Dataset suitability and reuse

Use existing D0 for code interpretation and figure reconstruction. P01/P02 public code and data schemas inform architectures and preprocessing, but currently do not establish a complete synchronized relaxation-history dataset with robot commands, forces and hidden-state evaluation labels. The [closest-work audit](closest_work.md) separates schema inspection from actual data access. Therefore D1/D2 must be generated with the project's information contract; D3 must be collected. Do not treat an object-deformation dataset as automatically answering state recoverability or action-value questions.

## 3. Physical history generation and matching

Generate histories by feasible commands from declared physical initial conditions, including loading, holds, release and recovery. Save the complete physical checkpoint; do not edit latent material fields to manufacture matched cases. Use only past/current **deployable channels** when selecting matched pairs for the main new benchmark. The old hidden-Jacobian-directed generator remains a labeled privileged mechanism experiment.

Match current position/velocity, force, command, tool/object pose, contact indicators, and every deployed visible side/surface feature within independently calibrated resolution. If filter memory is available to deployment, either include it explicitly or call the baseline current-delivered-signal rather than strictly instantaneous. Use independent sensor noise; byte-identical coupled noise is a diagnostic ablation only. Report channel-wise standardized residuals, maximum discrepancy, attempted/accepted counts and all rejection reasons.

Fix proposal seeds, loading bounds, matching algorithm and tolerances before final generation. Never filter final cases using future response magnitude, oracle action disagreement, candidate failure, or model prediction error. Maintain a second naturally sampled history population to estimate operational prevalence; do not pool the matched population into a natural-task claim. A negligible-effect case stays in the denominator and reveals the boundary of the phenomenon.

## 4. Minimal methods, held fixed wherever possible

| ID | Information and mechanism | Shared comparison contract |
| --- | --- | --- |
| M0 | Current delivered observations and context; capacity-matched instantaneous estimator | Same fitted physical predictor, action library and controller |
| M1 | Short-history classical observer; begin with 0.2 s, then a prespecified window sweep | Same observations/calibration; valid contact and initial-state assumptions documented |
| M2 | Full-history classical inference; plus a learned full-history initializer as a separately named variant | Same available reset information; no true test parameters |
| M3 | Carried recursive representation updated from latest action/arriving observation | All memory counted; same supervision and downstream predictor, or a factorial law comparison if sharing is impossible |
| M4 | True hidden state at the decision, with the **same fitted predictor** | Privileged state-information reference within this task/action/controller; not global optimum |
| M5 | True hidden state and true plant law | Diagnostic separation of model error and information error; not a deployable competitor |

Add a well-tuned reactive controller as a practical reference. If its action interface differs, report a native-controller result separately from the estimator-isolation comparison. A probability belief is added when point estimates collapse decision-relevant ambiguity; compare mean-only and calibrated distributional decisions with the same risk rule. Do not add a complex belief architecture merely to fill a method category.

All methods get the same sensor delivery, feasible actions, task thresholds, downstream control and computing deadline. Measure preprocessing, update, rollout and selection time separately. A method exceeding its deadline follows a common fallback/last-command rule while physical time advances. Hyperparameter and calibration budgets are logged. If M3 learns a different evolution law, cross encoder type and law type in a small factorial experiment before attributing gains to representation.

## 5. Evidence ladder with explicit next decisions

| Test / level | Controlled comparison and output | Support condition | Refutation or alternative explanation | Next decision |
| --- | --- | --- | --- | --- |
| X01 / V1: state relevance | Matched histories, same future commands; force/motion/shape response distributions | Future difference exceeds calibrated noise and numerical error across independent history units | Unmatched visible shape, parameters, actuator state, or solver artifact explains it | Fix matching/physics; stop hidden-state claim in that observation regime if no residual effect |
| X02 / V2-V3: recoverability and history needs | M0/M1/M2/M4; initial window grid 0, 0.05, 0.2, 0.5, 1, 3 s for the archived 0.15/1.4 s modes; recalibrate and freeze in time-scale/sampling units for the new carrier; ordinary versus informative intervention | History reduces held-out response uncertainty/error; window and action effects agree with observability conditioning | Learner failure mistaken for impossibility; prior/reset privileges; contact unavailable; ill-conditioned modes | Use shortest adequate history; add a justified probe or sensor if M4 shows task relevance but sensing is insufficient |
| X03 / V4: compression sufficiency | Frozen `z,r,c` predictor versus predictor also receiving older history; parameter-matched extra-capacity and shuffled/irrelevant-history controls | Residual-history gain interval lies below a task-linked prediction tolerance with sufficiently capable probes | Older history consistently improves held-out response/action ranking; weak probe cannot detect known omissions | Enlarge/change state or restrict scope; nonsignificance alone leaves the question open |
| X04 / V5: recursion | Full-prefix encoding and streaming updates evaluated at same cuts; held-out longer cycles | Both predictions remain accurate and calibrated against held-out outcomes, and agree within tolerance without re-reading the whole prefix | Two equally wrong predictors agree; drift, missing mode, filter-state omission, hidden buffer, or teacher-forced update | Repair explicit update/observation model before claiming online state representation |
| X05 / V6: action reuse | Encode once, replay checkpoint under prospectively selected new commands/gains; same state estimate | Predictions and action ranking remain adequate beyond training-policy futures | Conditioning on future actual displacement; future re-encoding; changed model/capacity | Fix interfaces; label action/controller transfer separately from carrier transfer |
| X06 / V7: decision benefit | M0-M4 under common controller and natural feedback, full operation constraints; M5 diagnoses law error | State access changes a chosen action and improves declared utility with an informative interval | No task headroom, weak candidate library, success ceiling, artificial delay, observer overwrite, or unequal information | Classify the four cases below; pursue method work only when an identifiable useful gap remains |
| X07 / V8: transfer scope | Freeze then separately allow bounded adaptation across named shifts | Prespecified effect survives the particular shift and adaptation cost is reported | New geometry called new mechanism; field labels or retuning leak test data | Claim only the supported transfer layer; another mechanism needs a new physical explanation and validation |

Use one primary metric per test: X01 paired response-effect magnitude versus the measured error floor; X02 force/shape predictive loss reduction; X03 residual-history predictive improvement; X04 streaming-versus-prefix forecast discrepancy; X05 held-out-action prediction error; X06 constraint-respecting completion or a preregistered utility with failure penalty; X07 degradation on the declared shift. Keep state-coordinate error diagnostic unless A is the explicit claim. State alignment by an arbitrary fitted rotation is not evidence of physical identification.

For the distributional definition of B in the formalization, X02-X04 also use a proper predictive score: CRPS for scalar force or an energy score for sampled multivariate responses, with interval coverage and sharpness diagnostics. Validate the score/probe on a deliberately omitted mode using training/validation data. RMSE alone tests conditional means, not distributional sufficiency; if no distributional estimator is implemented, explicitly narrow the supported B claim to mean responses and action rankings. Future forks may share exogenous random-number streams for paired variance reduction, but never share future measured observations with an estimator.

Define a practical prediction tolerance on independent calibration/pilot data by how forecast error can alter the declared force/deformation or action-ranking decision. Record it in physical units and normalized form. Require the numerical error budget to be smaller than that tolerance. All gate values remain **unfrozen** until this mapping is measured; no final test can be used to choose them.

## 6. The four-case discriminator

| Case | Evidence pattern under the fixed interfaces | Critical check before interpretation | Scientific response |
| --- | --- | --- | --- |
| 1: response-relevant, task-unnecessary | X01 positive, but M4 gives no useful X06 advantage | Test library/search/utility sensitivity; a weak state-reference controller can mask headroom | Report prediction relevance only or prospectively select a justified task; do not fabricate urgency |
| 2: useful, not recoverable under current sensing | M4 has decision value; even well-specified state inference leaves relevant ambiguity | Separate structural indistinguishability from finite noisy-data limits and algorithm failure | Maintain belief, add a realizable probe/sensor, or narrow achievable claims |
| 3: inferable, but feedback resolves it in time | History improves predecision forecasts; common feedback reduces relevant uncertainty before the consequential choice | Show truth/forecast improvement, not merely estimator convergence or covariance overwrite | Report feedback substitution boundary and keep the simple controller |
| 4: useful and inferable, but inference deficient | M4 headroom; available history contains needed information; current estimator loses it | Equal data, model fit, initial-state knowledge, compute and downstream controller | Target the identified inference/update deficiency; only now justify a new method |

Regimes can coexist. Report their prevalence in natural histories, with uncertainty, rather than assigning the entire research direction to one category.

### Special E3 diagnosis

Compare three **diagnostic** update modes after the same initialization: archived common covariance, validation-calibrated initializer uncertainty, and propagation without measurement innovations. Run both true-state/same-fitted-law M4 and true-state/true-law M5. Track physical state error, response uncertainty, action ranking and actual action change over the common prefix. A direct oracle-state handoff is a privileged diagnostic; a normal observer initialized once with truth is a different reference and may lose it. Name both accurately.

The main operational comparison retains ordinary credible feedback. Any extra-delay sweep is secondary. Select the decision cut and task timing before final access from the real operation, not by choosing where the candidate looks best.

## 7. Small data allocation and statistical status

Proposed initial spatial 2D allocation, conditional on one fixed carrier/parameter setting: 12 separate calibration trajectories; 24 independent pilot history blocks; 256 training history blocks; 64 validation blocks; and 128 fresh test blocks, split into 64 matched pairs and 64 naturally sampled histories. These are **planning values**, not existing data or adequate confirmatory power for every metric. Each paired block contains two histories and several future branches, all assigned together. History-seed blocks are independent conditional on this plant; they are not 128 independent material specimens.

The small package is for mechanism/effect-size estimation and route selection. With only 64 natural blocks, small binary success gains will generally be imprecise. Do not label it conference-level confirmatory robot evidence. The subsequent S3 robot study uses an independent pilot to size a fresh test population for a useful task-specific effect. The previous 640-block/two-task allocation is archived as an earlier scenario, not automatically inherited as a requirement.

Use at least three training seeds for the initial learned-model diagnostic and five for the later confirmatory study if feasible. Average or model training variation within independent physical/history units; do not count seeds, frames or branches as new physical samples. Resample whole blocks, and material instances first when reused, preserving predeclared strata and population weights. For a degenerate binary bootstrap, report discordant counts and appropriate exact/one-sided bounds rather than interpreting [0,0] as population equivalence.

Choose one primary model contrast on validation before final access; use Holm adjustment for a declared family of secondary comparisons. Report effects, intervals, per-seed outcomes, rejection/acceptance counts and failures. Pilot-based sample-size changes and threshold selection are prospective, before a new independent final set. Nonsignificance is not equivalence; an equivalence claim requires a meaningful margin and an interval/test appropriate to that margin.

Separate train, calibration, validation, independent pilot and test parent IDs. If measuring one real specimen repeatedly, treat repeated touches as within-specimen trials. New specimen/batch conclusions require independent specimens and grouped splits. Different future waits on the same E1 histories are dependent branches, not separate physical datasets.

## 8. Feasibility budget and logging

At the proposed test size, five primary estimator categories with one deterministic representative each would require `64*2 + 64 = 192` physical histories per method before action forks. Three learned-model seeds increase compute, not independent n. Profile generation, physics stepping, fitting and scoring separately on a small valid scene; record real-time factor and peak memory before expanding.

Set a prospective diagnostic cap of 8 local compute-hours for a timing/physics pilot, not a promise that continuum simulation fits. Record actual CPU/GPU use. The current local GPU exists but the project environment is CPU-only and lacks proposed 3D engines. Create a dedicated locked simulation environment; do not alter a working robot stack. Large baseline sweeps and the earlier 36,480-episode estimate wait for measured throughput and a discriminating task.

Every run stores code and dirty-diff hash, dependency/solver/asset versions, hardware, physical parameters, mesh/time steps, seeds, split parent IDs, calibration provenance, command and observation clocks, complete raw outcomes, model state/checkpoint, and failure categories. Count constraints over preload, probe, release, approach, task and retreat. Report task-window and full-operation metrics separately. Preserve failed trials, overruns, drops, divergence and solver errors; never silently remove them or overwrite old negative results.

## 9. Interfaces to implement before model expansion

Use the existing repository with English code/config/logs. Preserve `early experiment/` as archived evidence. Proposed modules are added only when implemented:

```text
src/nr/state/          # explicit physical state, estimate and belief contracts
src/nr/observations/   # calibrated channels, acquisition/delivery timing
src/nr/actuation/      # command, achieved input, controller and queue state
src/nr/carriers/       # 2D/3D hidden mechanism and valid physics range
src/nr/estimators/     # snapshot, short/full observer, recursive model
src/nr/tasks/          # one primary recontact/compression operation
src/nr/evaluation/     # X01-X07, grouped metrics, complete constraints
configs/              # declared parameters and separate planning/measured fields
data/manifests/        # immutable parent IDs and source hashes
runs/<run_id>/         # raw outcomes, timing, model state, failures
```

The core estimator contract is `initialize(history, context)`, `update(state, issued_action, delivered_observation)`, and `predict(state, robot_execution_context, future_command_policy)`. Return a typed estimate plus uncertainty/validity scope where supported. Explicitly serialize every retained state needed for restart. Add numerical/physics/reference checks that test real failure modes; do not fill the repository with empty modules or tests that merely restate implementation.

The machine-readable [eval_spec.json](eval_spec.json) records this plan and its unresolved gates. Passing its structural checker confirms required fields, not scientific validity or a working simulator.

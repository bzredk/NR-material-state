# Two linked frameworks, one research chain

The frameworks answer different questions. The overall framework determines whether a coherent research contribution is worth pursuing. The mechanism framework makes its physical explanation and evidence testable. Neither is a substitute for the other, and this is not a Cartesian product of all possible choices.

Status vocabulary: **ARCHIVED** = saved prior outcome; **ANALYZED** = inspected source/code without rerun; **PROPOSED** = design; **VERIFIED** = narrowly specified check actually passed; **UNKNOWN** = evidence missing. Paper assertions are additionally marked FACT, INFERENCE, UNKNOWN, or ACCESS_LIMITED in the comparison files.

## Stable IDs

- C01-C06 identify the same research chains in both matrices.
- Q1 = omitted dynamic information; Q2 = inferable, recursive, sufficient representation; Q3 = action value and transfer boundary.
- SRC-E1/E2/E3 = archived local experiments, SRC-AUDIO = recording/transcription evidence, SRC-WEB = research roadmap.
- P01-P17 retain IDs from the October 23 literature audit; T01-T04 add targeted theoretical foundations.
- D0 = existing synthetic histories; D1 = proposed synchronized spatial 2D histories; D2 = proposed articulated robot episodes; D3 = future calibrated physical measurements.
- X01-X07 identify experiments; V1-V8 identify claim levels. An experiment can support multiple levels, but success at a lower level never silently promotes the higher one.
- RQ-ARM, RQ-SENSE, RQ-SPECIMEN identify resource dependencies; they are not already acquired hardware.

## Overall research matrix

| Chain | High-level idea | Data | Scenario: conditions where the problem arises | Method: reason for considering it | Experiment: controlled evidence process | Carrier: object plus implementation setting |
| --- | --- | --- | --- | --- | --- | --- |
| C01 / Q1 | Current readings may omit action-relevant dynamic object state | D0 now; D1 later | Same geometry, parameters and current observable state; different feasible loading histories | Snapshot and true-physical-state predictions isolate missing information | X01 replay paired histories under common future commands; elastic negative control | Two-mode recoverable object; initially 1D model, then spatial 2D fixture simulation |
| C02 / Q2 | History can reduce state ambiguity only under adequate information conditions | D0/D1 with synchronized actions and measurements | Contact/free-space phases, different time constants, noise and available history | Short/full classical observers and history estimators distinguish information from model capacity | X02 vary history and informative contact intervals while holding model/data interfaces fixed | Same object/carrier as C01; sensor/clock qualification is a platform dependency |
| C03 / Q2 | A state representation should retain needed information and update recursively | D0/D1 stream with no future labels at deployment | Long episodes, interruptions, repeated release/recontact | Physical observer, recursive predictor, and belief approximation; audit every retained memory variable | X03 older-history residual-value test; X04 batch-versus-streaming and long-rollout consistency | Same carrier first; no new material needed to establish this question |
| C04 / Q2 | An inferred state should be reusable across relevant future actions | Matched D1 prefixes, held-out future commands/controllers | Same state, different pulse, dwell, speed or controller gain | Explicit action/controller conditioning rather than policy-specific history memorization | X05 fork the same physical checkpoint into predeclared future interventions | Same fixture, then one articulated arm/tool; changing controller is not changing mechanism |
| C05 / Q3 | For the action-value claim, prediction must change a useful decision in time | D1 mechanism and natural histories; D2 robot episodes later | Task constraints, sensing latency, feedback opportunity and action set jointly determine value | Common controller fed snapshot/observers/recursive state/true-state reference | X06 measure action changes, outcome gaps and feedback timing; audit observer overwrite separately | One rigid-tool recontact/press operation; lab-requestable arm and sensors conditional on interface checks |
| C06 / Q3 | Identify what transfers and what remains carrier-specific | Held-out D1/D2 groups; D3 only after collection | New action, instance, geometry, sensor, material family, mechanism and embodiment are separate shifts | Freeze or explicitly adapt components; account for adaptation data | X07 staged transfer with distinct claims and prospective splits | First same carrier; second task/other hidden mechanism only after a useful result |

## Mechanism and validation matrix

| Chain | Data: actual channels and availability | Physical carrier | Hidden-state mechanism | Action/task: executable intervention or objective | Method: information and assumptions | Validation level |
| --- | --- | --- | --- | --- | --- | --- |
| C01 | D0: issued reference, realized displacement/velocity, clipped force, known simulation fields for evaluation; D1 adds lateral shape | Two relaxation branches under unilateral contact | Same weighted internal-variable sum can hide different branch composition | Physically replay press/hold/release/wait; then apply identical future command | Snapshot vs true-state reference with the same physical transition model | V1 state relevance; SRC-E1 is scoped evidence, D1 is PROPOSED |
| C02 | C01 channels plus acquisition/delivery clocks, sensor calibration, noise model; no assumed infinite resolution | Same fixed carrier/parameters in primary contrast | Different decay rates can reveal branch composition during measured contact; detached zero force may only constrain an inequality | Short holds/recontact probes; probes count toward task time and constraints | 0.2 s classical observer, full-history classical, learned history estimator; state vs parameter inference separated | V2 recoverability; V3 history duration/excitation requirements |
| C03 | Causal streaming windows and all internal model memory; older history withheld only from the tested representation | Same carrier; no manual state surgery | Approximate memory compression may omit modes or accumulate update drift | Extend/repeat the same controlled contact cycle | Store all RNN h/c, observer covariance, context and filter memory; compare equivalent output predictions, not arbitrary latent coordinates | V4 empirical predictive sufficiency; V5 recursive consistency |
| C04 | Encode once at a cut; future command plans known, achieved motion not supplied from the future | Fixed checkpoint of same object/robot state | Same hidden composition interacts differently with different commands | Preregistered pulse/dwell/recontact/controller alternatives | Same inferred state and common action-conditioned forward model; no re-encoding future observations | V6 cross-action prediction; limited SRC-E2 support only |
| C05 | Deployable observations shared; true hidden state only in marked diagnostic reference; full episode logs | Recoverable specimen with calibrated valid range | Decision value requires differing feasible action values before feedback supplies equivalent relevant information | Reach/hold a deformation target under force bound, release, retreat; 3D arm performs all phases | Common finite action library/controller, matched inference budget; privileged true-state reference is restricted, not globally optimal | V7 decision benefit; SRC-E3 negative for its specific implementation |
| C06 | Grouped unseen instances/conditions; adaptation and calibration separately logged | Same material/new shape, new material law, different mechanism are separate cases | Mechanism invariance or failure must be diagnosed, not inferred from a new object label | Reuse declared intervention class, then a second task if justified | Freeze representation first; separately allow bounded adaptation; no privileged labels in primary deployment | V8 transfer scope; currently PROPOSED |

## Mapping between the axes

| Overall axis | Mechanism-framework role | How the pair is used to make a decision |
| --- | --- | --- |
| High-level idea | Hidden-state mechanism plus validation levels | An observed response difference establishes V1, not yet a general representation contribution |
| Data | Detailed data specification, action records and supervision access | Ask whether the information needed by the method is actually observable at deployment |
| Scenario | Conditions applied to carrier, sensing and action timing | A scenario is a regime; a probe/press/release is an intervention within it |
| Method | State definition, inference/update law and assumptions | A learned recurrent architecture merits testing when simpler alternatives leave an identified gap; classical observers are also recursive, and an empirical gap is not a necessity proof |
| Experiment | Assignment, controls, data splitting, comparisons and metrics | Validation level states which claim that experimental result can support, not another experiment name |
| Carrier | Physical carrier plus separately documented operation platform | Material/internal mechanism is distinct from arm, fixture, sensors, solver and computer; feasibility needs both |

Mappings are many-to-many. For example, C05 combines a feedback-timing scenario, a recontact task, a material carrier, and the X06 comparison, but only V7 concerns decision benefit. C03 can fail even if C01 succeeds. P01 can inform C02-C05 without proving all of them. These links are encoded in [registry.json](registry.json), rather than copying every source description into both tables.

## Cross-framework decision examples

1. **Problem validity:** C01 needs physically realizable histories and an effect beyond measurement/numerical error; a visually impressive nonlinear deformation is insufficient.
2. **Evidence sufficiency:** C03 requires older-history and recursive-update tests, not just a good next-force RMSE from C01.
3. **Method necessity:** C02/C05 must expose a gap after correct-family and short-history observers; a snapshot-only advantage does not select a neural method.
4. **Experimental discrimination:** X06 must separate task irrelevance, insufficient sensing, ordinary feedback recovery, and estimator deficiency; the same aggregate success rate can arise from all four.
5. **Platform feasibility:** C05 can use lab-requestable equipment only after RQ-ARM/RQ-SENSE are resolved. C01-C04 analysis and software interfaces can proceed without that answer.

# Research roadmap and decision record

Date: 2026-10-25. Status: evidence-based design; no new simulation, training, material test, or robot trial was executed. This document changes research scope and priorities, while preserving the archived experiments and their negative results.

The main question is **object hidden-state inference and representation**: what information from action-observation history must be retained to predict relevant interactions, update that understanding recursively, and determine when it is adequate for action? Recoverable material dynamics are the first physical carrier. Geometry, nonlinear response, lateral deformation and model mismatch provide observations or alternative explanations; none automatically becomes the research subject.

Use the linked C01-C06 chains in [frameworks.md](frameworks.md), the state definitions in [formalization.md](formalization.md), and the X01-X07 protocol in [minimal_experiment.md](minimal_experiment.md). This roadmap records decisions and prerequisites rather than duplicating those matrices.

## 1. Retain, revise, and leave open

| Judgment | Decision and evidence | Consequence |
| --- | --- | --- |
| Current observation can omit response-relevant state | RETAIN within SRC-history dependence's synthetic two-mode model. Physically replayed histories can share current readings while different branch states affect a common future response. | Continue C01; test whether the effect survives spatial observations, independent noise and numerical qualification. |
| History helps in the current model | RETAIN, with initialization and information qualifications. Full-history classical integration is more accurate than the learned estimator; the 0.2 s classical observer nearly matches the long-history network. | Preserve M1/M2 as serious baselines. Do not claim neural or long-history necessity. |
| An inferred state can be reused across futures | RETAIN the bounded SRC-controller transfer observation under tested commands/gains; revise its interpretation because comparisons also changed capacity and evolution law. | X05 freezes the estimate and separates representation, physical law and execution context. |
| Better prediction implies useful action benefit | REJECT as a general inference. SRC-shared feedback found no meaningful benefit in its shared-observer/controller setting; prefix-inclusive constraints also change the reported success level. | Run X06 with M4/M5, realistic common feedback and full-operation outcomes. Keep the negative result visible. |
| Material modeling defines the project | REVISE. The carrier supports a broader hidden-object-state question; constitutive-law learning is one component. | Judge methods by C01-C05 and actual information conditions, not by material complexity alone. |
| A small RNN code is a Markov state | NOT ESTABLISHED. All hidden/cell states, caches, filters and execution state count; P01 illustrates this distinction. | X03/X04 test predictive residue and recursive consistency without claiming a proof of minimality. |
| Robot/material implementation is ready | UNKNOWN. Equipment can be requested, but the user confirms no specimen, fixture or real measurements currently exist. | Obtain one working interface record and a small carrier calibration. Do not repeat the now-answered generic equipment-access question. |
| Broad hidden-state novelty is established | REJECT. P01/P16 already address history-based robot inference or interaction aliasing; P04/P14 establish dynamic internal-variable modeling. | Pursue a conditional, dimension-specific contribution and stop a claim when substantive overlap remains. |

Detailed evidence and limitations remain in [existing_evidence.md](existing_evidence.md), [closest_work.md](closest_work.md), and [resources_platforms.md](resources_platforms.md). A saved plan or runnable script is not a completed experiment.

## 2. Problem-Method-Insight contribution candidates

**Problem candidate.** For a fixed object mechanism and declared deployment observations, distinguish four situations: state changes response but is unnecessary for the task; state matters but is not recoverable; history recovers it but common feedback resolves uncertainty before the consequential decision; or useful information exists but an estimator fails to retain it. Physically replayed, matched-current histories and a natural-history population give this distinction an operational meaning. This is a candidate problem refinement, not evidence that partial observability itself is new.

**Method candidate.** Prioritize B, a predictive state with explicit recursive update and a defined validity scope. A, interpretable internal variables, supplies an instrumented reference; C, a probability belief, becomes useful if ambiguity remains relevant to decisions. No new method is established. First compare M0-M4 with the same fitted predictor and downstream controller. Develop a new inference or update mechanism only after a specific information-processing failure survives strong classical and compact recurrent alternatives. If another evolution law is needed, use the prescribed factorial comparison instead of attributing its gain to state representation.

**Insight candidate.** Identify the measured relationship between hidden-state time scales, sensor information, informative actions and decision timing that determines whether retaining history helps. A supported positive regime and a supported feedback-substitution regime could explain when physical understanding is adequate for a particular operation. This requires informative uncertainty bounds, not a collection of nonsignificant comparisons or an artificially delayed baseline.

**Conditional novelty paragraph.** We study when an object's evolving hidden state, inferred from physically realizable action-observation histories, remains useful for future robot interaction after every currently available observation and ordinary feedback are accounted for. The proposed contribution is a controlled evidence chain linking response relevance, recoverability, recursive retention, reuse across future commands and actual decision value, with explicit failure and no-benefit regimes. Its intended distinction from existing tactile physics inference, history-conditioned manipulation and constitutive-memory models is this jointly tested information-and-decision boundary under matched deployment conditions. That distinction must be supported by the experiments and rechecked against the closest literature; it is not a new claim for recurrence, beliefs, internal variables, or history-aware control by themselves.

| Dimension | Closest overlap | Evidence required for a substantive distinction |
| --- | --- | --- |
| Problem and information | P01 infers physics from interaction; P16 addresses observation aliasing with ordered wrench history. | C01/C02 must isolate evolving state at fixed parameters and show what the actual available channels do or do not identify. A different material name is insufficient. |
| Inference and state structure | P01 retains recurrent memory; P03 combines a learned prior with VI; P04/P14 evolve constitutive memory. | C03 must expose an identifiable failure and justify the proposed update/state structure under equal information. Calling a latent physical or adding an RNN is insufficient. |
| Cross-action and control | P01/P02 predict and plan; P16/P03 improve their demonstrated robot tasks. | C04/C05 must test reusable estimates, common control/feedback and decision headroom. A paper not reporting this exact test does not establish that its method cannot pass it. |
| Benchmark and insight | Existing papers have their own task-specific comparisons. | A qualified C01-C05 chain and meaningful scope test must provide a reproducible distinction or boundary that changes understanding or practice; relabeling baseline categories is insufficient. |

### Stop or narrow rules

1. **Literature collision:** if a closest work already covers the same core problem, information conditions, inference mechanism and principal insight, stop that novelty claim. State the matching work and exact overlap; a different simulator, material, sensor brand or network width does not rescue it. Retain a useful reproduction or benchmark only with its own justified contribution.
2. **No omitted-state effect:** if matching all deployed observations and qualifying physics removes X01's effect within a meaningful bound, stop the hidden-state claim for that observation regime. Investigate observable geometry, parameter differences or numerical artifacts.
3. **No method gap:** if an adequate short/classical observer meets the useful-effect tolerance, retain it and stop the claim that the proposed learned method is needed. Failure to reject a difference alone is not equivalence.
4. **No action headroom:** if M4 has no useful advantage after checking predictor quality, candidate-search adequacy, metric saturation and realistic timing, stop the action-benefit claim for this task/interface. H1 may still support a prediction or representation study.
5. **No recoverability:** if justified state inference leaves relevant uncertainty, do not force a point estimate. Add one feasible probe/sensor, maintain a belief, or narrow the task; distinguish structural limits from finite data or algorithm failure.
6. **Invalid advantage:** stop a robotics contribution whose effect depends on privileged future motion, weakened classical information, outcome-selected histories, unvalidated coupling or unrealistic delay. Correct the comparison before scaling it.

## 3. One primary task and a precise mismatch vocabulary

The primary operation is **recontact -> press to a target -> hold -> withdraw**, after a recorded loading/recovery history. Use one rigid rounded tool and one fixture-mounted recoverable specimen. Approach, preload, probing, release, retreat/reposition, recontact and final withdrawal all count toward time and constraint outcomes. The 3D version includes actual joint motion and actuator limits. Its cycle time and force/deformation envelope must come from a credible operating specification and calibration, not from a search for conditions favorable to a network.

The fixture reduces uncontrolled motion; it does not supply a hidden-state label. Side observations test whether apparent hidden-state effects are actually visible deformation differences. Later tasks or carriers test declared transfer axes only after this primitive provides discriminating evidence.

| Possible source of mismatch | Minimal distinguishing action | Interpretation |
| --- | --- | --- |
| Dynamic hidden state | Keep object parameters/context fixed; vary feasible history and replay common future commands. | C01-C04 question, if current deployed observations are matched. |
| Fixed unknown parameters | Separate calibration/context estimation from within-episode state inference; compare an AdaptiGraph-style property baseline when relevant. | Parameter uncertainty, not automatically dynamic memory. |
| Noise, filtering or timing | Measure static noise and dynamic delay; preserve acquisition/delivery clocks and actual execution. | Observation/execution uncertainty; more nominal samples do not undo filtering. |
| Wrong constitutive/contact/robot model | Compare M4 with M5 and independent force/contact/mesh checks before adapting a law. | Structural modeling error; a larger latent should not silently absorb it. |

Nonlinear response and hard/soft contrasts can be controls for these explanations. Deformation exceedance is not called damage without an appropriate model or measured criterion; stiffness alone is not a safety guarantee.

## 4. Stage gates: physics first, then inference and action

### S0: preserve evidence and define executable interfaces

Reuse archived D0 to reconstruct N1/N2, verify action/observation semantics and retain shared feedback's negative result. Freeze the meanings of state, parameter, command, achieved motion, history and context using [formalization.md](formalization.md). Prepare immutable parent IDs, access roles and the M0-M5 interfaces from the protocol. No empty module scaffolding is required now.

**Minimum exit artifact:** a source-linked evidence packet and a typed information contract; no new scientific result is claimed. A small 1D replay can diagnose software or shared feedback covariance behavior, but does not satisfy S2.

### B0: early material bench calibration, in parallel when resources arrive

Select a traceable specimen and loading fixture because neither exists yet. Record geometry, boundary conditions and temperature/context; obtain load-hold-release/recovery traces with force, displacement and side markers. Establish reversible operating range, repeatability, reset criteria, relevant time scales and measurement uncertainty. Include a simple elastic reference where feasible.

**Minimum action:** one small calibrated sequence plus repetitions sufficient to distinguish memory from sensor/repeatability error, with the number justified as a pilot. This is calibration, not confirmation of the hidden-state claim. Bench work may precede S3; physical robot manipulation may not.

### S2: spatial 2D mechanism and information study

Implement a spatial mesh/contact example with justified plane-strain or plane-stress assumptions, boundary conditions and lateral measurements. Qualify constitutive response against a reference relaxation/recovery solution; verify elastic/no-memory and zero-load limits, force balance, contact opening/recontact, and energy/dissipation behavior appropriate to the law. Test mesh/time-step convergence and parameter sensitivity. Numerical/contact error must fall below the task-linked evidence tolerance before learning comparisons.

Then generate D1 using feasible loading histories, independent sensor noise, current-channel matching and a separate natural-history sample. Run X01-X06 sequentially, starting with M0/M1/M2/M4. Fit the compact recurrent model only when the information or recursive-retention test calls for it. Normalize candidate history windows by measured or declared time scales and actual sampling, then freeze them using pilot/calibration data before fresh tests.

**Exit evidence:** qualified physics and sensing assumptions; X01 effect above error floors; recoverability/window evidence; a clear outcome for X03-X06 or an explicit narrowed claim. Advance a control-focused study only if a credible task has useful state-information headroom. Publish null regimes within the declared scope rather than deleting them.

### S3: complete articulated 3D closed-loop robot simulation

Select an arm asset after identifying the lab's actual usable model/controller. The proposed MuJoCo-SOFA/SofaViscoElastic integration is an engineering candidate, not a working stack. The resource-limited alternative is a qualified reduced hidden-mechanism carrier coupled to a full articulated arm; it supports narrower carrier claims and cannot establish real-foam or continuum-shape fidelity.

Before ML comparisons, qualify the complete plant:

- Robot joints, inertias, actuator/servo behavior, joint/velocity/torque limits, saturation and command transport are active parts of the simulation.
- Tool-object interaction produces equal and opposite reaction wrenches that alter robot motion; contact is not duplicated across solvers, and frames/units are tested.
- The 3D carrier has an explicit valid physical range and independently checked hidden dynamics. Generic soft geometry or prescribed deformation does not suffice.
- Multirate integration, time-step/mesh sensitivity, contact penetration, energy accounting and simple reference load cases pass stated numerical tolerances.
- Sensor acquisition, delivery, filtering, noise, dropouts and clock uncertainty are modeled from measured data where available; assumptions are labeled and swept where not measured.
- The entire operation, including approach and withdrawal, executes under the same causal controller and computing deadline for all estimator variants.

Only then run the M0-M4 comparison, M5 diagnostic, practical reactive reference, failure analysis and prospectively powered fresh test. Use independent history/specimen-model units and grouped splits, report all solver and task failures, and archive raw runs and versions. Animation, a kinematic end-effector trajectory or a successful demo is not this evidence.

**Exit evidence:** one complete task with qualified coupling, fair baselines, meaningful effect/uncertainty estimates, natural-feedback controls, failure accounting, and an independently reproducible configuration. This is the user's mandatory conference-level simulation gate before physical robot operation. No gate is currently passed.

### S4: physical robot operation, then limited transfer

After S3, deploy the same information contract on the confirmed arm/tool/sensors and calibrated specimen. Validate command-versus-execution timing and empty-tool force compensation first, then replay bounded complete operations. Predefine deviations from the simulated observation/action contract and report them as transfer conditions. Do not silently recalibrate on final tests.

First test same-mechanism transfer to physical measurements. Subsequently separate new specimen/geometry, material parameters, sensor configuration, future actions, embodiment and hidden mechanism. A second task tests task reuse; a second mechanism requires its own physical explanation and validation. Neither is required at the start, and changing shape alone is not cross-mechanism transfer.

## 5. Nadia feedback and thesis-role traceability

SRC-AUDIO consists of short archived recordings and transcriptions. The timestamped source transcript (local source: `2026-10-23-project-feedback/项目反馈总结与转录.md`) and source register (local source: `2026-10-23-project-feedback/sources.json`) are authoritative for this attribution; [the earlier decision record](../robot_manipulation/novelty_decision.md) preserves the prior interpretation. The direct English fragment is incomplete and speaker identity was not independently verified. Chinese recordings are post-meeting recaps, not verbatim teacher instructions. Upload/export dates do not prove the meeting date.

| Feedback ID and evidence type | Supported content | Our design response and verification artifact |
| --- | --- | --- |
| FB01: Chinese recap A, `Towne Building 2.m4a`, 00:00.500-00:06.000 | The teacher was reported to suggest 2D before 3D. | S2 precedes S3; spatial mesh, boundary conditions and side-response plots. The particular continuum approximation and solver are our choices. |
| FB02: Chinese recap A, 00:11.540-00:21.820 | Discussion questions simply presuming the force during manipulation; sentence is incomplete. | Model issued command and actual motion separately; measure/predict force as a coupled response. S2/S3 force-balance and bidirectional-coupling records. |
| FB03: Chinese recap A, 00:23.720-00:38.300; mismatch phrase approximately 00:34.8-00:38.3 | Hard/soft behavior, possible adverse deformation and mismatch were raised; crash/crush remains ambiguous. | Define mismatch by the table above; elastic control, model-law diagnostic and full-operation force/deformation limits. Do not infer a damage mechanism from the ambiguous word. |
| FB04: Chinese recap C, `University of Pennsylvania 2.m4a`, 00:00-00:15.820 | A highlighted figure showed lateral change after force was applied. | Measure lateral response in S2 and surface response in S3; match deployed geometry when isolating hidden state. Recover the original slide to verify the intended example. |
| FB05: direct English fragment B, `Towne Building.m4a`, 00:07.900-00:21.430 | Refers to a mesh slide and starts an example involving a robot with a single finger; ends before the conditions/conclusion. | Use a simple rigid-tool contact as our diagnostic design and show mesh-tool-joint coupling. The fragment does not prescribe our algorithm, task or physical law. |
| FB06: explicit current user instruction | Spatial 2D, then conference-level complete 3D arm manipulation simulation, then physical robot operation. | S2-S3-S4 ordering and the S3 gate above. This requirement comes directly from the user, not an inferred teacher mandate. |

The source does not establish Nadia's approval of a particular network, belief model, simulator, material, number of tasks, or proof claim. Lateral deformation can reveal an omitted **observable**; it supports a hidden-state claim only after its information is accounted for. Mismatch motivates diagnosing missing state versus wrong models, rather than making either explanation automatic.

The [research website](https://thesis-spine.link/thesis-spine-rendered) asks how embodied intelligence forms actionable physical understanding and knows when it is sufficient for action. SRC-WEB's organizing functions map to this project as follows:

- **Physical grounding:** C01/C02 relate units, measurements, actions and response-relevant state hypotheses to a qualified physical system.
- **Structured intelligence, Part I-to-II bridge:** C03/C04 test a reusable state plus an action-conditioned transition mechanism. They do not complete a neuro-symbolic architecture or establish causal discovery.
- **Reliable agency:** C05 measures when the estimate changes an admissible action, when ordinary feedback suffices, and when probing/fallback/defer is justified under declared uncertainty.
- **Part III active testing:** optional probes are equal-budget interventions after the basic information/decision gap exists; active probing itself is not claimed new.
- **Part IV transferable representation:** C06 tests specified compression and transfer limits; finite evidence does not prove universal sufficiency, minimality, uniqueness or safety certification.

## 6. Immediate actions and implementation priority

| Priority | Concrete action | Smallest evidence/output and dependency |
| --- | --- | --- |
| NOW | Preserve and present N1/N2/N3 from [existing_evidence.md](existing_evidence.md). | N1 uses a prespecified archived pair; N2 exposes classical success and shared feedback's negative result; N3 is labeled a proposed decision map. No invented new curves. |
| NOW | Finalize the state/observation/action schema and the narrow shared-controller comparison. | Typed interfaces, source-linked split manifest and full-operation metrics; use D0 without relabeling it spatial data. |
| NOW | Obtain the working device configuration through the confirmed request path. | Exact arm/controller/API/firmware, allowed modes, sensor mounting and one command/read-back/force/camera timestamp export. RQ-ARM/RQ-SENSE remain unmeasured until this exists. |
| NOW | Select one traceable specimen and fixture, and plan B0. | Sample identity, geometry, loading path, reset criterion and calibrated pilot; the user has confirmed these do not yet exist. |
| NOW | Build and qualify a small spatial 2D mechanism. | Constitutive/contact checks, mesh/time-step sensitivity, visible lateral response and an explicit observation model before neural fitting. |
| WAIT FOR S2 QUALIFICATION | Run X01-X06 in the minimal sequence and resolve shared feedback uncertainty treatment. | Physical matching residuals/acceptance, observer/window study, M4/M5 headroom and useful-effect intervals. Do not scale training before the discriminator. |
| WAIT FOR A DEMONSTRATED GAP | Adapt the closest useful learned method. | P01-style estimator/predictor or a compact recurrent baseline first; property fitting, VI or a constitutive learner only for the failure it addresses. Original-interface sanity check and source/version/license record precede reproduction claims. |
| WAIT FOR RESOURCE/PHYSICS RECORD | Complete S3 coupling and fresh confirmatory robot study. | Qualified full-arm operation, realistic sensing/limits, grouped statistical analysis, raw outcomes and reproduction instructions. |
| DEFER | Physical robot manipulation, multiple arms, VLA-scale training, several full-paper reproductions, grasp-transport, many carriers and broad mechanism transfer. | Reconsider after preceding evidence supports their scientific value; B0 calibration can proceed earlier. |

Keep new code/configuration/logs/technical documents in English and in the existing organized project. Add modules only when implemented, isolate simulation dependencies, pin assets and solver revisions, and serialize all estimator/execution memory. The concrete layout and logging requirements are in [minimal_experiment.md](minimal_experiment.md); no global environment modification or hardware upgrade is required by this planning document.

## 7. Next Nadia discussion: judgments and unresolved decisions

We can already say that SRC-history dependence supports partial-observation aliasing in a prescribed synthetic family; correct classical inference is strong; a short window can suffice in that regime; SRC-controller transfer supports bounded future-control reuse; and SRC-shared feedback does not establish action value. We cannot yet claim spatial validation, learned recursive sufficiency, a novel inference mechanism, calibrated material realism, or robot-control benefit.

Bring N1, N2 and N3, with sources and status labels, and use them to resolve three concrete issues:

1. Which practical recontact/press operation has a consequential choice that may precede feedback resolution, with a defensible cycle time and force/deformation envelope?
2. Which working arm/tool/force/side-view configuration should be recorded first, and which traceable specimen/fixture can expose reversible memory above measurement error?
3. If classical inference already suffices, is the desired contribution a carefully established information/decision boundary, or should the project seek a different identifiable inference difficulty? Recovering the original mesh/lateral-response slide will also resolve the incomplete recording's example.

These are scientific and implementation decisions, not requests to approve an already invented algorithm. Until they close, continue the source-backed formalization, physics qualification and minimal experiment preparation; keep unresolved quantities explicitly marked rather than promoting planned values to measurements.

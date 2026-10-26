# Novelty decision and research role

## Decision

**No-go for the current broad method claim. Conditional go for a narrower empirical research question.** This is a decision to stop arguing that generic history-to-state prediction is new, not a claim that all investigation of material memory is exhausted.

The project currently supports two limited observations: history can improve next-contact prediction relative to an instantaneous snapshot, and a history-derived initialization can be reused under several future controls. Neither establishes a new constitutive representation or useful robot decision improvement. The archived E3 comparison found no meaningful action gain after common causal feedback.

## Claims that collide with existing work

| Proposed claim | Closest overlap | Why the residual difference is insufficient |
| --- | --- | --- |
| Encode tactile history into latent physics and use it for planning | [RoboPack](https://www.roboticsproceedings.org/rss20/p130.pdf), Sec. III-C/E, PDF pp. 5-6 | History estimation, autonomous prediction, and MPPI are already one system. Changing the object to a viscoelastic pad does not establish a new framework. |
| Learn internal material variables and their evolution | [PANN viscoelasticity](https://arxiv.org/abs/2401.14270), [Evolution TANN](https://arxiv.org/abs/2209.13269), [memory/material RNO](https://arxiv.org/abs/2502.05463) | These already represent history with evolving internal variables. Neural rates, compact states, and constitutive structure are not new by themselves. |
| Predict force from loading, waiting, and unloading history | [Viscoelastic Hertzian contact LSTM](https://arxiv.org/abs/2607.19060), Sec. 2-3 and Appendix G | Time-resolved contact-force prediction across such phases is directly addressed. A different recurrent cell or loading curve is insufficient. |
| Same current observation can require different actions because of history | [HIRE](https://arxiv.org/abs/2609.30828), Sec. III-IV | Visual aliasing, wrench history, and a fast execution loop already motivate and implement this claim in real manipulation. Material memory must be isolated from contact progress and task phase. |
| Identify material properties online, then adapt manipulation | [AdaptiGraph](https://arxiv.org/abs/2407.07889), including Appendix C | Static property identification, multiple-property identification, and uncertainty-driven probes are already investigated. |
| Separate material context from dynamic memory | [Learning Memory and Material Dependent Constitutive Laws](https://arxiv.org/abs/2502.05463), Eq. 2.4 | Material context explicitly conditions an evolving memory model. A context/state split alone is not a defensible contribution. |
| A small learned latent is the unique or minimal physical state | [Internal-variable identifiability](https://arxiv.org/abs/2605.14179), Theorem 4.11 | Existing identification results require strong reachability, convexity, and transformation assumptions. Sparse boundary measurements and a latent-size sweep do not establish these assumptions. |

Important distinctions: RoboPack freezes its inferred physics vector during each future prediction rollout, but its estimator updates the vector from observations. PANN uses its auxiliary LSTM during training, then deploys a constitutive integration law. HIRE predicts future wrench as a training auxiliary signal and uses history in a real feedback policy. None should be described as simply having no memory. An experiment absent from a paper is not proof that its method cannot pass that experiment.

## Current project evidence limits

The saved [results](../../early%20experiment/RESULTS.md) report E1 force RMSE of 0.003680 N for history, 0.052179 N for snapshot, 0.000234 N for the correctly specified classical estimator, and 0.003695 N for a local 0.2 s observer. The held-out wait is interpolation within the training range. E2 changes future controls but the GRU comparison also changes model capacity and evolution law. E3 reports a 0 percentage-point safe-success difference and no meaningful completion-cost benefit under common feedback. These are archived results, not reruns performed in this audit.

These observations reject the argument that beating the snapshot baseline demonstrates a need for a neural world model. They also prohibit turning better open-loop prediction into an assumed safety or control benefit. Earlier one-dimensional experiments remain one-dimensional even if their internal state has two coordinates.

## Conditional research question

For a fixed material law, geometry, and matched current observable state, can a deployable estimate of residual material memory improve constrained robot action selection before ordinary feedback resolves the relevant uncertainty? Where does this advantage disappear as sensing, feedback rate, action duration, or material relaxation time changes?

This question requires physically replayed histories, equal information, common feedback, commands rather than privileged future motion as model inputs, and a correctly specified classical observer. Evaluate both selected matched-observation mechanisms and a natural task population. Otherwise a curated ambiguity demonstration can manufacture an advantage that does not matter for normal operation.

### Candidate contribution paragraph, not a validated novelty claim

We investigate when a reusable material-state estimate is actually necessary for robot decisions under contact feedback. The proposed study separates residual material memory from static parameter uncertainty and geometric mismatch, constructs physically replayed histories with matched current observations, and tests the same state estimate across future robot commands and controllers. Its intended contribution is an empirically supported boundary between cases where material memory changes constraint-respecting action choice and cases where ordinary feedback or a classical constitutive observer is sufficient. Such a result would connect material-state inference to actionable physical understanding; it would not claim that recurrent constitutive models, latent physical parameters, or history-aware control are new. This contribution remains conditional on substantial effects against strong baselines, validated physics, and generalization beyond one synthetic model family.

There is currently **no defensible paragraph claiming a novel algorithm**. If a new method becomes necessary, specify its mechanism only after identifying a failure not resolved by existing observers and recurrent models. A benchmark contribution also needs a reproducible, broadly useful question and evidence beyond a contrived distribution; renaming a task or adding a dimension does not meet that standard.

## Nadia feedback traceability

The audio files are short and partly retrospective. The following table preserves source attribution rather than converting student recaps into verbatim faculty requirements. The directory date is retrieval/upload context, not independently verified meeting date.

| Evidence | Interpretation | Required study response | Verification artifact |
| --- | --- | --- | --- |
| `Towne Building 2.m4a`, roughly 0-6 s, Chinese recap | Start with 2D, then 3D | Real spatial plane-strain contact precedes 3D articulated manipulation | Mesh, boundary conditions, lateral-marker plots, stage gate |
| Same file, roughly 11.5-21.8 s, Chinese recap | Do not simply assume the force | Contact force is an output of material/contact/robot dynamics; the robot applies a command | Force-balance and two-way coupling tests; command/measurement logs |
| Same file, roughly 23.7-38.3 s, Chinese recap; one word ambiguous | Address hard/soft behavior, deformation risk, and mismatch | Elastic control, recoverable viscoelastic material, material-law mismatch, measured force/deformation bounds | Constraint metrics over the entire episode, model-family ablation |
| `University of Pennsylvania 2.m4a`, roughly 0-15.8 s, Chinese recap | Applied load should explain lateral material response | Observe side displacement in 2D and surface deformation in 3D; match these when isolating hidden memory | Side-marker trajectories and matched-observation diagnostics |
| `Towne Building.m4a`, roughly 7.9-21 s, direct English fragment | Returns to a mesh slide; mentions robot and a single finger; sentence incomplete | Keep a simple contact mechanism for diagnosis, then establish the robot interaction explicitly | Mesh-to-tool-to-joint-dynamics diagram and executable scene |
| Latest user instruction | Conference-level simulated robot manipulation before hardware | Complete 3D closed-loop robot tasks, comparisons, statistics, and reproducibility before physical robot trials | Robot benchmark report and gate decision |

The fragment does not establish a complete Nadia-approved algorithm, material, controller, or proof requirement. Hard material is not assumed safe, and deformation is not labeled damage without a damage model or calibrated physical criterion.

## Role in the live research roadmap

The [roadmap](https://thesis-spine.link/thesis-spine-rendered) asks how an embodied agent builds actionable physical understanding and knows when that understanding is sufficient for action. Its three organizing functions are physical grounding, structured intelligence, and reliable agency.

| Roadmap function | Concrete contribution this project can make | Claim to avoid |
| --- | --- | --- |
| Physical grounding | Map actions and sensor histories to force, deformation, and material-state hypotheses with units and calibrated uncertainty | A latent vector is automatically a physical quantity |
| Structured intelligence; bridge from Part I to Part II | A reusable state plus a conditional transition law whose scope can be tested across actions | Low prediction error establishes a causal operator or completes the neuro-symbolic architecture |
| Reliable agency | Determine when to reuse the estimate, collect a bounded probe, fall back, or defer | A finite empirical test is a universal safety certificate |
| Part III, active testing and revision | Optional equal-budget probes after the basic decision effect is established | Information-gain probing itself is novel |
| Part IV, sufficient transferable representation | Empirical compression and transfer under a declared action class | Minimality, uniqueness, or universal sufficiency has been proved |

The deliverable should therefore be a scoped statement such as: "Under this sensor set, material family, action class, and feedback timing, the representation improves these decisions with this uncertainty." It should also report conditions where the representation adds no value. Both outcomes serve the roadmap more faithfully than preserving a neural-method claim regardless of evidence.

## Decision rules

1. If matching all deployable observations removes the history effect, stop the hidden-memory claim; the earlier gain was observable geometry or omitted measurements.
2. If a classical observer matches the learned estimator within a preregistered useful-effect margin, retain the classical solution and drop the claim that neural state inference is necessary. A non-significant test alone is not evidence of equivalence.
3. If common feedback erases the useful action benefit, stop the control-advantage claim for that regime. Report the negative boundary.
4. If an advantage exists only with artificial sensing delays, weakened baselines, privileged future motion, or same-solver artifacts, do not advance a robotics claim.
5. If the full comparison supports a useful and transferable effect, develop the narrow empirical contribution. Re-audit novelty before inventing a new method label or submission claim.

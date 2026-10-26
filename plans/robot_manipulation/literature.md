# Primary-source literature audit

Audit date: 2026-10-23. Seventeen full papers were downloaded and extracted. The pages listed below were inspected for methods, relevant experiments, or appendices; this is **targeted full-text reading**, not a claim that every proof and every page was verified. PDF page numbers are one-based file pages. Four pages were also rendered to check diagrams and equations against extraction: RoboPack p. 5, PANN p. 8, HIRE p. 4, AdaptiGraph p. 15.

The source PDFs, extracted text, URLs, retrieval timestamps, and SHA-256 hashes are in `../../../Documents/Codex/2026-10-23-novelty-experiment-audit/source_manifest.json`. Search scope and access limitations are in that directory's `search_ledger.md`. This is a focused, reproducible nearest-work audit, not an exhaustive systematic review with a fabricated screening count.

## Closest work by mechanism

| ID | Work | Main overlap | Main distinction to test, not assume |
| --- | --- | --- | --- |
| P01 | RoboPack | Tactile history, latent physics, forward prediction, MPPI | Evolving residual material state versus a physics vector frozen during rollout |
| P04 | PANN viscoelasticity | Learned internal variables and constitutive evolution | Sparse robot boundary observations and useful closed-loop decisions |
| P08 | Viscoelastic Hertzian-contact LSTM | Loading/dwell/release history to contact-force trajectories | Command-driven articulated interaction rather than prescribed future indentation |
| P14 | Memory/material RNO | Separate material context and evolving memory | Partial observability and robot decision effects |
| P16 | HIRE | Observation aliasing, ordered force history, fast robot feedback | Material-memory mechanism rather than contact-event/task-progress memory |
| P02 | AdaptiGraph | Property identification, adaptive manipulation, active probing | Within-material residual state rather than only property estimation |

The distinctions in the last column are experimental questions. Their absence from a paper's reported evaluation does not demonstrate an incapability of its method.

## P01 — RoboPack: Learning Tactile-Informed Dynamics Models for Dense Packing

[RSS 2024 primary paper](https://www.roboticsproceedings.org/rss20/p130.pdf); [project](https://robo-pack.github.io/). Inspected pp. 3-9, 14-15; visual check p. 5.

The object state combines particles and a latent physics vector. Graph message passing predicts particles; an LSTM updates the physics vector using tactile history (Eq. 8). During a future rollout, the vector is frozen and no future tactile observation is supplied. Particle-trajectory MSE trains estimation and prediction jointly (Eq. 9). MPPI selects robot actions and replanning incorporates new observations. This is a direct predecessor of a history-estimate/predict/control decomposition.

Real Franka experiments include pushing and dense packing with vision and Soft-Bubble sensing. The pushing table reports 16/20 successes for RoboPack, versus 8/20 without tactile input. Its physics comparison lacks tactile observations, so it is not an equal-information comparison to copy unchanged. The paper does not isolate residual viscoelastic memory using matched current observations, but its recurrent estimator must remain a strong competing explanation.

## P02 — AdaptiGraph: Material-Adaptive Graph-Based Neural Dynamics for Robotic Manipulation

[RSS 2024 primary PDF](https://hauserlab.web.illinois.edu/papers/RSS2024-Zhang-AdaptiGraph.pdf); [arXiv](https://arxiv.org/abs/2407.07889). Inspected pp. 3-9, 13, 15-16; visual check p. 15.

A graph dynamics model conditions on material category and continuous properties; particle inputs include three position time steps. Real observations refine properties using predicted-versus-observed geometry. Bayesian optimization or CMA-ES performs identification; manipulation uses model-based planning. It is therefore inaccurate to call the model entirely memoryless.

Experiments cover rigid boxes, ropes, granular objects, and cloth with an xArm6 and RGB-D sensing. Appendix C already investigates joint stiffness/friction identification and an uncertainty-driven interaction objective. The latter does not consistently outperform the paper's motion-based selection in its rope examples. The relevant missing controlled test is residual state at fixed material parameters, not the generic idea of online adaptation or informative probing. An adapted baseline should preserve its temporal inputs and property fitting budget.

## P03 — Rapid Mismatch Estimation via Neural Network Informed Variational Inference

[CoRL 2025 / PMLR 305](https://proceedings.mlr.press/v305/jaszczuk25a.html); [PDF](https://raw.githubusercontent.com/mlresearch/v305/main/assets/jaszczuk25a/jaszczuk25a.pdf). Inspected pp. 3-8, 18-19.

Jaszczuk and Figueroa infer added end-effector mass and center of mass from a short joint-torque-residual window. A convolution/attention network produces a prior mean, then mean-field variational inference estimates the physical mismatch. The modeled residual is a gravitational wrench associated with these parameters, not a general viscoelastic contact force. The architecture uses a 200 ms data window and a small inference model; experiments include real Franka compensation.

Identifiability depends on excitation and pose; some center-of-mass components are poorly observable near vertical alignment. Stability/passivity statements have specific ports and assumptions and cannot be transferred verbatim to a coupled deformable-contact system. The useful connection is informed inference with uncertainty. A material-state adaptation changes the likelihood and latent variables and must be labeled RME-inspired, not a reproduction of original RME results.

## P04 — Viscoelasticity with physics-augmented neural networks: Model formulation and training methods without prescribed internal variables

[Primary preprint](https://arxiv.org/abs/2401.14270); [Computational Mechanics 2024 publication](https://link.springer.com/article/10.1007/s00466-024-02477-1). Inspected pp. 3-9, 12-14, 16; visual check p. 8.

The constitutive model uses a generalized-standard-material formulation: free energy and a convex dissipation potential define stress and internal-variable evolution through a Biot relation. Neural potentials impose structural restrictions. An auxiliary LSTM learns internal variables from strain, stress, and time increments during training. At deployment, that auxiliary network is discarded; the learned potentials are integrated using an implicit solver. This training/inference distinction matters.

Synthetic small-strain viscoelastic data include nonlinear response and noisy observations. The tested internal state is one second-order tensor, not an unrestricted guarantee of identifying every material's hidden state. The work directly covers learning internal variables and evolution without prescribing their values. It does not establish sparse boundary-sensor observability or robot closed-loop utility. Those are additional inference/control problems, not reasons to ignore the constitutive prior art.

## P05 — Recurrent neural networks learn the constitutive law of viscoelasticity

[Primary PDF](https://www.gchenlab.com/assets/pubs/RNN-VE.pdf), Computational Mechanics 2021, DOI 10.1007/s00466-021-01981-y. Inspected pp. 1-8.

The reference model is an isotropic small-strain generalized Maxwell material with recursive internal relaxation variables. LSTMs learn stress from strain sequences and propagate hidden/cell states to predict later increments. The paper therefore already demonstrates learned recurrent memory and state reuse. Data comprise fixed-material loading sequences, including linear and stepped histories; extrapolation to other temporal profiles is tested and large jumps can cause difficulty.

The problem supplies material-point strain inputs, rather than recovering a distributed state from robot boundary forces and images. No manipulation control advantage is established. The paper's hyperparameter discussion also uses test performance; our protocol must use validation data instead. This is a necessary recurrent constitutive baseline, while direct numerical comparison requires matching units, material laws, information, and task interfaces.

## P06 — Evolution TANN and the identification of internal variables and evolution equations in solid mechanics

[Primary full text](https://arxiv.org/abs/2209.13269), JMPS 2023, DOI 10.1016/j.jmps.2023.105245. Inspected pp. 1, 4-9, 15, 21; not all proofs or supplementary examples verified.

Free energy defines stress, while a continuous-time neural evolution law propagates latent internal variables. For unknown internal variables, an encoder compresses microscopic coordinates and training uses reconstruction, derivatives, constitutive outputs, and dissipation terms. The evolution law can subsequently run without the microscopic encoder; an optional decoder reconstructs fine-scale information. Negative dissipation is penalized in training, which is not a blanket guarantee for arbitrary learned weights and unseen states.

Examples concern inelastic constitutive response and homogenized systems. Fine-scale coordinates and derivatives provide substantially richer training information than a robot's force/camera stream. This work overlaps with compressed physical state plus learned evolution, but a fair sparse-sensor comparison cannot silently provide microscopic state to only one estimator. Separate privileged constitutive references from deployable boundary-observation baselines.

## P07 — History-Aware Neural Operator: Robust Data-Driven Constitutive Modeling of Path-Dependent Materials

[Primary full text](https://arxiv.org/abs/2506.10352), inspected v2, 2025. Pages inspected: 3-8, 11-16, 18-21, 24, 35-36, 39.

HANO combines Fourier and local neural operations with attention over a finite strain/stress history. A known next strain increment conditions stress prediction; predictions are appended autoregressively. Scheduled teacher forcing and noise injection address rollout error. Its memory is a history window rather than a persistent constitutive recurrent state.

Experiments include elastoplasticity, anisotropic damage, preloaded starting states, temporal resolution changes, and loading extrapolation. History-length saturation is empirical and dataset-specific, not a universal sufficiency theorem. The work already tests partially observed loading history, so a window-length sweep alone is not novel. An adapted robot baseline must consume future commands and predict realized motion, rather than receiving actual future deformation. Its original material-point task cannot be equated with boundary-state inference without that adaptation.

## P08 — Deep learning-based prediction of time-resolved adhesive forces in viscoelastic Hertzian contacts

[Primary full text](https://arxiv.org/abs/2607.19060), inspected v2 dated 2026-10-01; treated as a preprint. Inspected pp. 7-8, 10-15, 23-24, 44-45.

Boundary-element simulations combine a standard-linear-solid half-space and adhesive traction law. Loading, dwell, and unloading are represented on a phase-based time grid, with physical time supplied explicitly. The dataset contains 12,446 trajectories. Eighteen sequence architectures/conditioning variants are compared; an LSTM is the best reported model. Inputs include indentation history, derived causal features, and material/contact context.

This directly overlaps with predicting force from viscoelastic interaction history. The paper examines interpolation and withheld parameter bands, but does not demonstrate robot closed-loop manipulation. Known future indentation in a constitutive/contact surrogate is not the same as a future robot command: contact reaction changes realized motion. Nonadhesive robot experiments also require a different contact law. These distinctions define additional experiments, not an automatic novel-model claim.

## P09 — Context-Aware Force Estimation for Deformable Tool Manipulation in Robotic Environmental Swabbing via Few-Shot Continual Adaptation

[Primary full text](https://arxiv.org/abs/2607.07574), 2026 preprint. Inspected pp. 2-7.

A UR5e provides wrist wrench, joint position, velocity, and torque histories. LSTM features plus context conditioning estimate current tool-tip force, with a calibrated tip sensor supplying training targets. Few-shot adaptation addresses tool/surface combinations. This is a real-robot precedent for separating context from recurrent interaction history, including fast inference.

The output is current tip force, not a command-conditioned branch of future interaction, and autonomous feedback-control integration is left for future work. Architecture descriptions differ between sections about hidden width and which parameters are adapted; these must be resolved before claiming a faithful reproduction. For the proposed wiping task, it is an especially relevant adapted estimator baseline. Its reported errors should not be copied as newton-valued results without checking the calibration and units used in each table.

## P10 — Meta-SysId: A Meta-Learning Approach for Simultaneous Identification and Prediction

[Primary full text](https://arxiv.org/abs/2206.00694), 2022; venue not needed for this audit. Inspected pp. 3-6.

A shared predictor is conditioned on a task context optimized from a support sequence. An outer training objective rewards query prediction; an exponential-moving-average model supports context optimization. Context inference and dynamics prediction are therefore already separated and reused across observations.

The relevant distinction is between estimating a task's persistent parameters/context and maintaining a material's evolving residual state. This paper is background against claims of first separating adaptation from prediction. The inspected methods and mass-spring setup do not establish the proposed material-memory experiment; later examples were not used to make detailed claims here. A context-only baseline should receive the same calibration sequence, and parameter-fitting iterations must count toward adaptation cost.

## P11 — Tactile Probabilistic Contact Dynamics Estimation of Unknown Objects

[Primary full text](https://arxiv.org/abs/2409.17470), 2024. Inspected pp. 2-6.

The model combines quasi-static planar contact mechanics, a learned geometry representation, pose/scale/friction parameters, and known impedance control. A particle filter estimates parameter uncertainty from wrench observations. Candidate probing actions are evaluated by expected information gain. The state is primarily a belief over uncertain object/contact parameters; the model is not a constitutive residual-memory model.

Simulation compares active, random, and expert interactions. Real UR5e experiments use expert exploration, so the real results should not be represented as a full real-robot validation of the active policy. Reported planning time also differs from high-rate control. This is direct prior art against generic claims that uncertainty-driven physical probing is new. Its rigid/quasi-static assumptions limit direct transfer to viscoelastic manipulation.

## P12 — SoftMAC: Differentiable Soft Body Simulation with Forecast-based Contact Model and Two-way Coupling with Articulated Rigid Bodies and Clothes

[Primary PDF](https://minliu01.github.io/SoftMAC/static/pdfs/SoftMAC.pdf); [project](https://minliu01.github.io/SoftMAC/), IROS 2024. Inspected pp. 3-7.

SoftMAC couples MLS-MPM soft dynamics to articulated rigid dynamics and cloth. Forecast contact adjusts grid velocities toward particle contact constraints. Two-way coupling sends rigid poses/velocities to the soft solver and returns contact reaction to the articulated system. The paper includes a seven-DoF Franka pouring task and other optimized manipulation sequences.

This provides a concrete precedent for physically interacting robot simulation, not just a moving visual mesh. Its documented corotated elastic, plastic, and fluid models do not establish the relaxation spectrum needed here. A viscoelastic extension would require constitutive and coupling validation. Differentiability is useful for optimization but is not itself a test of physical fidelity. We use SoftMAC as a coupling reference and an alternative implementation route, not as proof that the desired material is already supported.

## P13 — Differentiable Particles for General-Purpose Deformable Object Manipulation (DiPac)

[Primary full text](https://arxiv.org/abs/2405.01044), 2024. Inspected pp. 1, 3-7.

RGB-D observations initialize particles; a differentiable MPM model fits physical parameters from demonstrations using geometric losses. Candidate manipulation trajectories combine sampled actions and learned proposals, followed by optimization and replanning. Real Kinova examples include rope pushing, granular sweeping, and cloth hanging; pouring is evaluated in simulation.

The work already joins parameter calibration, physical rollout, and robot planning. Its reconstruction assumptions and geometric objectives should be kept visible when adapting it to occluded, force-constrained contact. The inspected experiments do not isolate material-state memory under matched current observations. A direct transfer would need a recoverable viscoelastic constitutive law and an observation model for force, rather than merely renaming a particle parameter as history.

## P14 — Learning Memory and Material Dependent Constitutive Laws

[Primary full text](https://arxiv.org/abs/2502.05463); [SMAI Journal of Computational Mathematics 2026](https://smai-jcm.centre-mersenne.org/articles/10.5802/smai-jcm.148/). Inspected pp. 3-8, 24-25, 27-28, 31-32; full proofs not audited.

The FNM-RNO formulation conditions both constitutive output and memory evolution on material microstructure (Eq. 2.4). Thus material context is not merely an initial-state code. Homogenized heterogeneous viscoelasticity supplies a memory mechanism; theoretical approximation results apply to specified settings, and numerical examples include viscoelastic and inelastic response.

The results show that a small latent dimension can work well empirically while exact representation may require more modes. Latent-size saturation does not prove a unique minimal state. This is a major collision with the general context-plus-evolving-memory claim. The available microstructural input and prescribed constitutive loading differ from sparse robot measurements; establishing useful inference from those measurements remains a separate problem.

## P15 — A Neural-Network Framework to Learn History-Dependent Constitutive Laws and Identifiability of Internal Variables

[Primary full text](https://arxiv.org/abs/2605.14179), inspected arXiv version submitted 2026-05-13. Its metadata also lists related JMPS DOI 10.1016/j.jmps.2026.106807; the publisher version was not accessible for verification, so technical claims here refer to the archived arXiv text. Inspected pp. 3-6, 9-11, 16-18; complete appendix proofs not verified.

An energetic formulation couples learned stored energy and dissipation to neural internal-variable evolution. Structural conditions address physical invariance and constitutive properties. Identification results are conditional: Theorem 4.11 relies on assumptions including strict convexity, suitable reachability, smoothness, and a state-coordinate relationship. They do not guarantee that arbitrary sparse robot histories uniquely recover physical internal variables.

Numerical constitutive examples, including a polycrystal model, demonstrate accuracy with compact latent states. This source blocks a casual claim that learning a compact, physically constrained hidden state is new or automatically identifiable. Our study can test predictive sufficiency within a declared sensor/action distribution, but must not promote that empirical finding to the theorem's conclusion.

## P16 — HIRE: History-Conditioned Interaction Reasoning and High-Rate Execution for Visually Aliased Precision Manipulation

[Primary full text](https://arxiv.org/abs/2609.30828), 2026 preprint. Inspected pp. 2-7; visual check p. 4.

The arXiv page says code will be released upon publication; availability of a faithful runnable release was not established in this audit.

HIRE explicitly addresses visually similar observations that require different actions because interaction history differs. Ordered wrench traces become force-event tokens for a slower reasoning model; a faster recurrent executor uses local physical feedback and cached context. Future-wrench prediction is an auxiliary training objective, not future sensing at deployment. The reported reasoning and execution rates are 5 Hz and 50 Hz.

Real Flexiv experiments include transparent-object handling, connector manipulation, and a rotary latch, with ordered/current/shuffled-history comparisons. This is a serious collision with generic history-aware manipulation under aliasing. The proposed study's distinct question is residual constitutive memory at fixed material and matched observations, plus its survival under common feedback. HIRE does not prove that distinction is useful, and its policy should not be dismissed because it lacks our proposed state interpretation.

## P17 — Estimating Tactile Models of Heterogeneous Deformable Objects in Real Time

[Primary PDF](https://motion.cs.illinois.edu/papers/ICRA2023_Yao_VolumeStiffnessField.pdf), ICRA 2023, DOI 10.1109/ICRA48891.2023.10160731. Inspected pp. 3-6 and introduction.

A volumetric stiffness field represents independent elastic responses. A contact simulator tracks contact and stick/slip displacement; joint torques become linear observations of stiffness. A projected diagonal Kalman filter plus replay of prior observations makes large fields tractable. Real Kinova interactions with artificial plants evaluate torque prediction under overlapping and unseen touch locations.

Replay improves estimation of static stiffness; it is not viscoelastic material memory. Contact points return to their reference position on detachment, and viscoelastic/plastic extensions are described as future work. This supplies a strong structured estimation precedent, especially if heterogeneous stiffness becomes part of our benchmark. It also illustrates why stiffness, contact geometry, and residual relaxation must be distinguished experimentally.

## Access-limited and excluded leads

- [Modulation and Time-History-Dependent Adaptation Improves the Pick-and-Place Control of a Bioinspired Soft Grasper](https://link.springer.com/chapter/10.1007/978-3-031-72597-5_24), Living Machines 2024: publisher abstract and lab description inspected, full chapter not obtained. It is a potential overlap in history-dependent grasp adaptation, but no detailed method or negative novelty claim is based on inaccessible text.
- Long-horizon semantic/action-memory papers surfaced in search but were excluded from the nearest constitutive-memory set unless their physical interaction mechanism was verified. Title similarity alone did not qualify them as a deep-read source.
- Several 2026 items are preprints. Their relevance does not depend on an unverified claim of conference acceptance.

## Implications for comparison design

The mandatory evidence is not a table of weak memoryless baselines. It is an equal-information comparison against a fitted classical constitutive observer, a recurrent command-conditioned predictor, a short-history model, and adapted latent-physics/property models. Use original authors' code where feasible, record commit and modifications, and label adaptations honestly. For material-point methods, strain/stress field access is privileged unless an equally available observation model reconstructs it. For policy methods, separate native-policy comparison from the controlled experiment that holds the planner fixed.

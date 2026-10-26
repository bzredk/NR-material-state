# Closest methods, information contracts, and reusable implementations

Audit date: 2026-10-25. Status: primary-source and code inspection; no external model was installed, trained, or reproduced. This update reuses the 2026-10-23 archive and its page-level reading ledger. It adds targeted paper checks and public implementation/data checks, rather than repeating a broad search.

Evidence labels: **F** = explicitly stated in the paper or directly inspected source code/metadata; **I** = a reasoned implication of that mechanism; **U** = not established by the inspected evidence; **A** = access or release limitation. Absence of an experiment is never treated as inability of the method.

Stable paper IDs remain P01 RoboPack, P02 AdaptiGraph, P03 RME, P04 PANN, P14 memory/material RNO, and P16 HIRE. They connect to C01 response relevance, C02 recoverability/history, C03 compressed/recursive sufficiency, C04 action reuse, C05 decision value, and C06 transfer scope in the main research matrices. Public-data IDs below are D-P01, D-P02, D-P03, D-P04, and D-P16; these must not be confused with the project's own datasets.

## 1. What changes in the research interpretation

The subject is inference and representation of hidden object state. Constitutive learning is one mechanism and carrier literature line, not the definition of the subject. P04 and P14 restrict claims about inventing material internal variables or learning their evolution; they do not by themselves refute a sparse-observation object-state research program. Conversely, P01 and P16 are direct robot-level precedents for using physical history to resolve partial observability and select actions. Generic history encoding, latent prediction, context/state separation, or adding recurrence cannot be the contribution claim.

The unresolved question must be stated at a specific information and decision interface: which histories distinguish currently aliased physical states, which compact update retains relevant distinctions, which future actions test it, and whether decisions improve before ordinary feedback removes the ambiguity. The inspected works do not collectively prove that this exact experiment has already been exhausted, but the absence of an identical experiment is not novelty evidence by itself.

## 2. Five priority method records

### P01 - RoboPack (RSS 2024)

Sources: [paper](https://www.roboticsproceedings.org/rss20/p130.pdf), [project](https://robo-pack.github.io/), [pinned source tree](https://github.com/BoAi01/robopack/tree/ac02a01006b50dbb7379b676ec5a622921875c5b). Reused reading pp. 3-9, 14-15; rechecked pp. 6-7, 14 and source files listed below.

| Field | Evidence |
| --- | --- |
| Research question | **F:** Infer object physics and geometry from vision/touch despite occlusion, then predict and plan pushing/packing. |
| State definition | **F:** Object particle positions plus an object-level physics vector, dimension 16 in the paper. A graph estimator updates particles and physics from observations; a distinct predictor rolls forward without future tactile measurements. |
| Actual observations | **F:** Initial/periodic visual point clouds, Soft-Bubble deformation and optical-flow-derived tactile features; vision is available between pushes and only initially for packing. |
| Actions and execution | **F:** Straight-line push macro-actions are decomposed into tool motions; MPPI controls execution through Deoxys OSC_POSITION/OSC_YAW. **F, code:** `dataset.py` constructs model action features from realized in-hand/tool particle displacements. **I:** A command-conditioned dynamics benchmark needs an explicit command-to-realized-motion interface; copying this action representation unchanged can give extra future-motion information. |
| History | **F:** Training prose samples the estimation/prediction cut within a 25-frame sequence; Appendix Table V also lists a 15-step training history. Planning histories are 22/25 steps for pushing/packing. **U:** The exact correspondence between prose, table, and each released training configuration needs reproduction-level reconciliation. |
| Recurrence and state accounting | **F, code:** `EstimatorDPINet` has a two-layer LSTM and retains `lstm_hn_cn`. Config `history_length=1` refers to graph input at a recurrent step, not one-frame memory. **I:** The emitted 16-D vector alone is not all retained estimator memory; claims about a compact recursively sufficient state must count hidden/cell state too. |
| Training supervision | **F:** Joint estimator/predictor training uses object-particle trajectory MSE; tactile autoencoder is trained separately. The physical vector has no explicit material-parameter label. |
| Deployment information | **F:** Future prediction uses predicted particles, actions, and the physics vector frozen during that rollout. Observational updates can change the vector later. |
| Assumptions | **F:** Object/particle processing, rigid and nonrigid motion decomposition, contact-neighborhood graph, and task-specific action abstraction. **I:** These are not a proof of Markov sufficiency under all physical actions. |
| Scenario and carrier | **F:** Rigid boxes with changed mass distributions and compliant in-hand tool behavior; multi-object dense packing including deformable objects. Static unknown properties and contact/tool state both matter. |
| Platform | **F:** Franka Panda, two Soft-Bubbles with internal D405 cameras, four external D415 cameras, custom adapters, Deoxys control; learned model uses real interaction data rather than requiring a soft-body simulator. Pymunk is a comparison. |
| Baselines | **F:** No-tactile ablation, RoboCook plus tactile, and a fitted physics simulator. **F:** The physics baseline estimates properties from vision, so it is not equal-information to the tactile model. |
| Split and data | **F:** Three box configurations train, a fourth differs in appearance/mass distribution; packing has train/test object sets. The paper reports about 12,000 pushing and 6,000 packing frames. **F, code:** Separate train/validation directories are loaded. **U:** The released sample's full parent-episode and object split manifest was not verified. |
| Contribution boundary | **F:** Tactile-informed state estimation, prediction, and MPC are already integrated. **I:** A controlled test of residual state at fixed parameters, command-conditioned prediction, and sufficiency under shared feedback is a different evidence contract; it is not automatically a new model. |
| Reproduction limits | **A:** README sample Drive link returned 404 through the connector and was inaccessible to the web tool. This means access was not established, not that the dataset is proved deleted. **F:** Repository metadata reports no license and no LICENSE file was present in the inspected tree. **U:** Complete data provenance and reproducible end-to-end hardware setup remain unresolved. |

### P16 - HIRE (arXiv v1, 2026-09-25)

Sources: [versioned full text](https://arxiv.org/html/2609.30828v1), [PDF](https://arxiv.org/pdf/2609.30828v1). Reused reading pp. 2-7; rechecked pp. 5-6 and release statement. Relevant links: C01-C03 and C05; C04 is not established merely by policy success.

| Field | Evidence |
| --- | --- |
| Research question | **F:** Visually similar interaction states require different next actions depending on preceding physical events; combine persistent history with precise contact execution. |
| State definition | **F:** An interaction-state reasoner produces force-event tokens and cached cross-rate context; a recurrent interaction-manifold executor outputs intrinsic progress, transverse correction, desired wrench, and force/position selection. **I:** This is a task/interaction representation, not a recovered constitutive internal state. |
| Actual observations | **F:** Global/wrist RGB-D, motion/proprioceptive feedback, ordered six-axis wrench history; camera use differs by task. Publication visualization viewpoints are explicitly not all policy inputs. |
| Actions | **F:** A slower continuous-action policy handles free motion; contact execution uses structured motion plus hybrid force-position regulation and hysteretic switching. |
| History | **F:** Wrench stream at 100 Hz is pooled to 25 Hz for the reasoner, which runs at 5 Hz; executor runs at 50 Hz with local motion-wrench history. **U:** A single universal numeric maximum history duration and all timestamp/delay details were not established in the inspected text. |
| Supervision | **F:** Demonstrations supervise actions and structured execution variables; subsequent measured wrench is an auxiliary training target. **I:** This is privileged future supervision during training, not future sensing at deployment. |
| Deployment information | **F:** Past wrench, current vision/motion, cached context, and local feedback; future-wrench auxiliary head is not required at inference. |
| Assumptions | **F:** Contact mode switching and meaningful task-specific interaction manifolds; pretrained pi0.5 reasoner with learned fast execution. **I:** Policy architecture and task structure must be separated from the representation effect in a fair comparison. |
| Scenario and carrier | **F:** Transparent-object probing/pick-place, EV connector mating/demating, quarter-turn latch. These include hidden contact progress and retained interaction-event evidence, not just soft materials. |
| Platform | **F:** Flexiv Rizon 4S, Flexiv-GN01 two-finger gripper, six-axis force/torque sensor, two Orbbec Gemini 2 cameras. |
| Baselines | **F:** Native pi0.5, pi0.5 plus current wrench, TA-VLA, ForceVLA, FM-VLA, RDP, Force Policy, plus ordered/current/shuffled-history analysis. |
| Split and data | **F:** 300 real demonstrations per task, synchronized visual observations, wrench histories and executed actions; 30 evaluated rollouts per task with cumulative stage success. **U:** A downloadable dataset, independent object-instance grouping, precise train/validation split files, and raw command/execution timestamp schema were not verified. |
| Contribution boundary | **F:** History aliasing plus fast closed-loop operation is already demonstrated. **I:** Generic claims of using history to make observations Markov or action-relevant strongly overlap. Testing constitutive state at fixed parameters is more specific, but HIRE's unreported performance there cannot be assumed poor. |
| Reproduction limits | **A:** The primary page still states code will be released upon publication. No runnable author release was established. A small history-conditioned feedback baseline must be labeled an adaptation, not reproduced HIRE. |

### P02 - AdaptiGraph (RSS 2024)

Sources: [paper](https://hauserlab.web.illinois.edu/papers/RSS2024-Zhang-AdaptiGraph.pdf), [project](https://robopil.github.io/adaptigraph/), [pinned source tree](https://github.com/Boey-li/AdaptiGraph/tree/a7c75357793422e9108c36f58c6928f3f8a123ad). Reused pp. 3-9, 13, 15-16; rechecked pp. 4, 6-7, 13 and README/config. Relevant to C02, C04-C06 with parameter/state distinction.

| Field | Evidence |
| --- | --- |
| Research question | **F:** Predict/manipulate materials with unknown physical properties using a conditioned graph model and few-shot parameter optimization. |
| State definition | **F:** Particle graph, material category M, continuous property phi, robot/end-effector particles, and recent particle positions. Properties are shared within an object. |
| Actual observations | **F:** Four calibrated RGB-D views yield object point clouds. Material type is assumed known. Main formulation does not require a contact-force measurement. |
| Actions | **F:** Pushing/pulling or grasp-drag trajectories enter dynamics as end-effector motion; MPPI chooses interactions and task actions. |
| History | **F:** Paper describes h=3 prior-position history; released rope config uses `n_his: 4`, consistent with retaining current plus preceding samples. Adaptation accumulates completed interactions. It is not a zero-history baseline. |
| Supervision | **F:** Simulator particle trajectories with known randomized physical parameters; MSE over three prediction steps. |
| Deployment information | **F:** Material type, point clouds, action trajectories, and a property estimate fitted to interaction outcomes. Parameter fitting uses BO for one dimension and CMA-ES for multiple dimensions. |
| Assumptions | **F:** Properties lie in modeled families; graph perception and category-specific assets are available. Exploration maximizes predicted displacement; Appendix C also tests joint stiffness/friction and uncertainty-driven selection. |
| Scenario and carrier | **F:** Box center of pressure, rope stiffness, granular size, cloth stiffness; primarily unknown fixed properties within an episode. |
| Platform | **F:** xArm6, parallel gripper or task-specific printed stick/flat pusher, four D455 cameras at 15 Hz and 1280x720, 70 x 45 cm workspace. FleX generates deformable data; Pymunk generates box data. |
| Baselines | **F:** Unified GNN, separate GNN, no adaptation, simulator parameter fitting, and unconditional-model fine tuning. |
| Split and data | **F:** Original generation uses 1,000 episodes/material with five interactions each; README reports 900/100 training/validation. Public sample has 100 episodes/material with 98/2 split, reflected in released config. Paper separately reports evaluation on 200 simulated objects per material. **I:** Public sample validation is a smoke-test resource, not reproduction of the full statistical study. |
| Contribution boundary | **F:** Online property identification and adaptation already exist. **I:** Evolving residual state at fixed properties is a distinct target, but the short history can encode some dynamics; superiority must be tested. |
| Reproduction limits | **F:** MIT repository, Python 3.9/PyTorch 2.2.1/CUDA 12.1/RTX 4090 reported tested; PyFleX generation uses Linux Docker/NVIDIA tooling. **U:** Compatibility with this project's Windows/GPU environment and a viscoelastic recovery law is not established. |

### P03 - Rapid Mismatch Estimation (CoRL 2025)

Sources: [paper](https://proceedings.mlr.press/v305/jaszczuk25a.html), [project](https://mateusz-jaszczuk.github.io/rme/), [pinned source tree](https://github.com/mateusz-jaszczuk/RapidMismatchEstimation/tree/a2fe683ccc7a921692949445f867a73938933d89). Reused pp. 3-8, 18-19; rechecked pp. 7-8, 18-19, README and inference source. Relevant to C02, C05, uncertainty and platform constraints.

| Field | Evidence |
| --- | --- |
| Research question | **F:** Rapidly infer added end-effector mass/center of mass and compensate manipulation dynamics mismatch without an external force/torque sensor. |
| State/parameter definition | **F:** theta = mass and three center-of-mass coordinates; Gaussian variational posterior. **I:** These are piecewise constant unknown parameters within each inference window, not a constitutive state evolving under every action. Abrupt load changes trigger re-estimation. |
| Actual observations | **F:** Joint position and external-torque-residual histories, robot kinematics and nominal dynamics. Pseudo-wrenches are derived through the Jacobian. |
| Actions | **F:** Existing impedance/velocity-based controller executes static holding, limit-cycle tracking, and interaction tasks. The estimator itself is not an explicit future-action world model. |
| History | **F:** 200 ms collected window, reduced to 20 pseudo-wrench tokens for the neural prior. Appendix compares 50/100/200/300 ms and uses 11 real datasets; reported total adaptation includes collection and inference. |
| Supervision | **F:** Simulation with known mismatch parameters trains a convolution/attention prior; a likelihood based on the physical wrench model refines the estimate using VI. |
| Deployment information | **F:** Proprioception, robot model, pretrained prior and likelihood; no future trajectory or external FT required by the original formulation. |
| Assumptions | **F:** The modeled mismatch is gravitational payload wrench; observability depends on pose/excitation. Compensation/passivity results have the paper's controller/port assumptions. **I:** They cannot be transferred wholesale to deformable contact. |
| Scenario and carrier | **F:** Robot-held payloads/basket and changed mass distribution; human perturbation can temporarily confound estimation. |
| Platform | **F:** Torque-controlled Franka with CPIC in the paper. The current official project also shows PVIK pick-place with qb SoftHand2 Research and OptiTrack; this is separately identified project evidence. |
| Baselines | **F:** VI with neural versus zero prior mean, nominal versus RME-augmented control, collection-window ablation. |
| Split and data | **F:** 350 simulated parent trajectories produce 1,050 time-shifted inputs split 80/20; additional time-translated test data and 60 real static experiments are reported. **U:** Whether parent simulations were grouped before the augmented-window split is not established. Do not copy this split description as leakage-proof. |
| Contribution boundary | **F:** A learned prior plus probabilistic physical inference is prior art. **I:** Material-state inference needs a new likelihood/state transition and observability analysis; call it RME-inspired if adapted. |
| Reproduction limits | **F:** Public Python/ROS inference, weights and normalization files exist. Source contains robot-specific FK and hardcoded `/home/mateusz/...` paths. **U:** Full training data, training pipeline, dependency lock and end-to-end controller release were not established from the inspected tree. No root license was found and API license metadata is null. |

### P04 - Physics-augmented viscoelastic internal-variable models (Computational Mechanics 2024)

Sources: [published article](https://link.springer.com/article/10.1007/s00466-024-02477-1), [archived preprint](https://arxiv.org/abs/2401.14270). Reused pp. 3-9, 12-14, 16; rechecked pp. 9, 12-13 and published method sections. This is carrier-modeling context for C01-C03 and C06, not a replacement for the object-state research subject.

| Field | Evidence |
| --- | --- |
| Research question | **F:** Identify thermodynamically structured viscoelastic constitutive laws without prescribed internal-variable training labels. |
| State definition | **F:** Strain and internal inelastic-strain tensor q; free energy and dissipation potential determine stress and q evolution. The examined reference has one internal second-order tensor. |
| Actual observations | **F:** Material-point strain/stress paths and time increments; these are not directly equivalent to a robot's net contact wrench and surface image. |
| Actions | **F:** Prescribed strain histories for constitutive evaluation, including multiaxial and restricted loading paths. |
| History | **F:** Auxiliary LSTM carries hidden/cell state during training. It is discarded after training; a constitutive integration law propagates q at inference. |
| Supervision | **F:** Stress mismatch plus constitutive residual; synthetic experiments also use known q in a separately described reference comparison. |
| Deployment information | **F:** Strain/increments, initialized q, learned potentials and numerical integration. **I:** Recovering an unknown q after arbitrary unobserved prehistory is an additional observer problem, not automatically solved by discarding the training LSTM. |
| Assumptions | **F:** Small-strain generalized-standard-material setting and a restricted constitutive structure. Finite-strain robot contact is outside the demonstrated setting. |
| Scenario and carrier | **F:** Synthetic nonlinear viscoelastic material-point responses, ideal/noisy stress and uni-/bi-/multiaxial loading. No physical robot or sensor apparatus is used in the reported experiment. |
| Platform | **F:** Numerical constitutive generation/training; FE deployment is described as an application but not addressed experimentally in the paper. |
| Baselines and splits | **F:** Integration-based training, auxiliary FNN and auxiliary RNN; random spline paths with training variants such as 1x200 and 100x100; a separate generated 250-increment test path. Multiple training attempts are compared by final training loss. **I:** This does not constitute an independent robot/object-distribution benchmark. |
| Contribution boundary | **F:** Learning internal variables/evolution with physical structure is established. **I:** That limits a constitutive-method novelty claim but does not settle inference from sparse robot measurements or task-relevant sufficiency. |
| Reproduction limits | **U:** No author code/data repository was established from the inspected preprint and published page. Equations and generation recipe support a documented reimplementation, not a claimed exact reproduction. |

P14, [Learning Memory and Material Dependent Constitutive Laws](https://arxiv.org/abs/2502.05463), remains a related boundary source: material context conditions an evolving memory law, so the context/dynamic-state distinction itself is not new. It supplies a constitutive reference, not evidence that robot boundary sensing is sufficient. The prior reading record is retained rather than redoing the entire paper.

## 3. Experimental architectures and the role of each channel

| Paper | Robot -> tool -> object -> control/prediction | Information for inference | Training/evaluation-only information | Effect of an equipment substitution |
| --- | --- | --- | --- | --- |
| P01 | Panda -> Soft-Bubble-held rod/object -> weighted boxes or packing set -> graph estimator/predictor + MPPI + Deoxys | Dense tactile deformation/flow; object point cloud at permitted observation times | Tracked particle trajectories supervise dynamics; object class can analyze latent clusters | Replacing dense touch with one wrist wrench changes the observation map and may remove shape/contact localization. It is an adapted information condition, not identical reproduction. |
| P16 | Flexiv -> GN01 gripper -> transparent objects/connector/latch -> slow reasoner + fast manifold executor | Ordered wrench events, motion and camera views | Future-wrench targets, action/structured-execution demonstration labels; separate illustration views | A position-only arm or much slower wrench stream may invalidate execution assumptions. A generic small recurrent controller can test history benefit but is not HIRE. |
| P02 | xArm6 -> printed stick/flat pusher or parallel gripper -> box/rope/granular/cloth -> property fit + graph dynamics + MPPI | Multiview shape change reveals fixed property | Simulated physical parameters and particles for training | A side camera plus net force may be better for a low-dimensional relaxation mechanism, but does not preserve their dense shape input or material categories. |
| P03 | Franka -> payload/basket; project additionally SoftHand2 -> CPIC/PVIK + mismatch compensation | Joint torque residuals and changing kinematics reveal gravitational mismatch | Known simulated mass/CoM; calibrated loads for scoring | Without reliable torque residuals and model calibration, external FT is a new information condition. It may help, but the original no-external-sensor claim no longer transfers. |
| P04 | Numerical strain driver -> material point -> stress/internal-variable integration | Full strain and stress paths during identification | Reference internal variables in labeled comparisons | Net boundary force is not local stress; surface geometry is not the full strain tensor. A boundary observer or FE inverse problem is required. |

These are configurations observed in this five-work reading sample. They do not establish that any arm, tactile sensor, simulator, or control rate is a field-wide standard. They also do not establish local project ownership or access; see the resource audit.

## 4. Public data suitability audit

Legend: **F-schema** means explicitly documented or consumed by inspected code; **F-paper** means reported in the paper but not verified in a downloadable payload; **U** means unknown; **not documented** does not prove absence from every unreleased recording.

| Dataset | Commands vs realized motion | Force/touch and shape | Time/history/reset | Identity, parameters, hidden-state truth | Directly useful for this project |
| --- | --- | --- | --- | --- | --- |
| D-P01 RoboPack sample | **F-schema:** processed actions derived from realized tool displacement; EE/joint states are recorded. Raw issued-command availability in the released archive **U**. | **F-schema:** object/bubble point clouds, force-like tactile fields; recorder lists bubble force and flow. Absolute force calibration in released data **U**. | **F-code:** stamped ROS topics and synchronization logic. Actual residual timing error, complete preloading/recovery, and initial internal condition **U**. | **F-code:** object class field. Physical parameter/internal stress labels and split manifest **U**. | Replay graph/tactile pipeline and test predictive integration if sample access is restored. Cannot currently certify matched-state relaxation or commanded-action sufficiency. |
| D-P02 AdaptiGraph simulation sample | **F-schema:** action vector and realized `eef_states`, particle positions. | **F-schema:** particle deformation; optional validation color/depth. Force is not in the documented HDF5 schema. | **F-schema:** `info.timestamp` is described as number of frames T, not acquisition/delivery timestamps. Explicit recovery/reset history for viscoelastic state is not documented. | **F-schema:** `property_params.pkl`, episode grouping, randomized properties. Constitutive fast/slow state labels not documented. | Smoke-test property-conditioned prediction, preprocessing, and parameter fitting. The current data do not establish a residual-memory benchmark. |
| D-P02 real demo | **F-release listing:** `granular_1.zip` and per-interaction NPZ layout in README. Binary fields were not inspected. | **U** beyond point-cloud/action role reported in demo code description. | **U** physical-time and history completeness. | **F-paper/README:** coffee-bean granularity example, not hidden relaxation truth. | Demonstrate few-shot parameter optimization; not an independent physical memory dataset. |
| D-P03 RME | **F-interface:** joint-position and external-torque histories. Raw command, Cartesian execution and synchronization archive **U**. | **F-paper/interface:** torque residuals; no external FT needed. Object surface deformation is not part of model. | **F-paper:** 200 ms windows and shifted examples; full experiment-time reset manifests **U**. | **F-paper:** simulated mass/CoM labels. **A:** full data and generation pipeline not found in inspected repository tree. | Test inference software on newly generated, robot-specific payload data; cannot reuse weights as material-state labels. |
| D-P16 HIRE | **F-paper:** executed actions in synchronized demos; raw command vs measured-motion separation **U**. | **F-paper:** six-axis wrench and visual streams. Distributed deformation/internal-state truth not reported. | **F-paper:** ordered histories; public timestamp/reset schema **U**. | Contact-stage demonstrations; physically unique object state labels and object-group split manifests **U**. | Architectural comparison and demonstration design guidance. No direct public-data experiment is currently established. |
| D-P04 PANN | Prescribed strain input; robot commands/realized robot motion not applicable. | **F-paper:** strain and stress tensors, synthetic ideal/noisy response. | **F-paper:** physical time and increments; reference loading starts from specified zero strain. General unknown-prehistory observer data not established. | **F-paper:** reference law parameters and q labels available to generator; label-free and labeled training comparisons distinguished. | Constitutive law verification and controlled material-point tests after reimplementation. It does not solve the sparse-sensor robot observation problem. |

### Data access checks on 2026-10-25

- P01 README points to Drive file `1KS9Zyp4Z9K7R0F13zmgMpsP21Wa589C2`; metadata request returned 404 under the current connector. The public web tool also could not access it. Do not claim the ZIP has been inspected.
- P02's [public release folder](https://drive.google.com/drive/folders/1HR39B7PXbYkM2w3XcA3feTCRCZH1q7UG) was listed through Drive. It contains `sim_data`, `model_ckpt`, `perception_ckpt`, and `demo_data`. The simulation folder lists granular.zip (686,064,449 bytes), cloth.zip (476,828,964), and rope.zip (868,133,700); the demo folder lists granular_1.zip (135,041,249). These payloads were not downloaded; schema assertions come from README/code, not binary inspection.
- P03 source tree contains inference code, ROS wrapper, model weights and normalization files; no full training/evaluation dataset was identified there.
- P16 explicitly defers code release. P04 code/data availability was not established. These limitations prevent calling any of these a ready-made dataset for the complete proposed evidence chain.

The smallest useful public-data follow-up is one original-task smoke run for a selected baseline, accompanied by actual payload schema and split inspection. A fresh project simulation dataset is still required for physically replayed matched histories, known hidden states, commands and realized motion, and controlled future branches. A physical dataset must additionally log calibration, synchronized acquisition/delivery times, reset criteria, specimen identity, and all loading/recovery prefixes.

## 5. Versioned implementation reuse

| ID | Verified source revision | Reusable component | Necessary adaptation or blocker |
| --- | --- | --- | --- |
| K-P01 | RoboPack `ac02a01006b50dbb7379b676ec5a622921875c5b`, commit dated 2025-03-21 | Estimator/predictor split, recurrent graph state, MPPI structure, tactile preprocessing and recording interfaces | Count all recurrent memory; bridge commands to realized motion; replace sensors explicitly; resolve sample access and reuse license before redistributing derived code. No installation was tested. |
| K-P02 | AdaptiGraph `a7c75357793422e9108c36f58c6928f3f8a123ad`, commit dated 2024-07-25, MIT | Graph dynamics, property optimization, split/preprocessing templates, simulator generation code | Replace fixed-property-only target with a separate dynamic-state experiment; validate physical law; port legacy PyFleX/Linux dependencies only if needed. Avoid treating the 98/2 sample split as final evaluation. |
| K-P03 | RME `a2fe683ccc7a921692949445f867a73938933d89`, commit dated 2025-08-20 | Neural-prior/VI interface, asynchronous ROS inference pattern, robot-residual plumbing | Change robot FK and hardcoded paths; retrain for changed embodiment; derive material likelihood/transition if adapting. No root license or full training pipeline established. |
| K-P16 | No runnable author release established | Method-level design and ablation concepts | Implement a clearly labeled smaller control adaptation; no reproduction claim or copied paper scores. |
| K-P04 | No author repository revision established | Constitutive equations and data-generation recipe | Document independent implementation; material-point stress/strain inputs need an observation model for robot use. |

The three inspected code repositories do not constitute evidence that the entire required robot/material stack is compatible. A backend qualification and one original-task sanity check precede a benchmark adaptation. Public availability also does not establish that current project hardware supports the same sensor/control interfaces.

## 6. Novelty dimensions cannot substitute for each other

| Dimension | Already covered by closest work | A legitimate project-specific question | Evidence needed before a claim |
| --- | --- | --- | --- |
| Problem setting | Partial observability and history aliasing: P01/P16 | Residual evolving state at fixed parameters, with all current deployed observations matched | C01 plus explicit alternative-explanation controls |
| Available information | Dense tactile, vision, proprioception, or full strain/stress in different papers | Sufficiency of the actually available sparse channels and excitation | C02 observation-map audit, uncertainty and identifiability tests |
| Inference mechanism | Recurrent encoders, parameter optimization, neural prior plus VI | A demonstrated failure of existing estimators under matched information | C02-C03 against well-specified classical and recurrent baselines |
| State structure | Object particles/latent physics, constitutive internal variables, interaction context | A representation with explicit retained memory, recursive update, and no older-history predictive residue in a declared scope | C03; retain all hidden/cell/cache variables in state accounting |
| Theory | Belief and predictive-state sufficiency have established foundations | A new theorem only if assumptions/conclusion differ materially | Formal statement and proof; empirical compression alone is insufficient |
| Cross-action prediction | Forward models and replanning already appear in P01/P02 | Same inferred state tested under controlled future commands/controllers, without privileged future motion | C04 with fixed encoder and separated execution model |
| Control value | P01/P16/P03 demonstrate benefits in their tasks | Whether hidden-state knowledge matters before common feedback repairs it in our task | C05, same action library/controller/compute, including null-benefit regimes |
| Benchmark/insight | Each paper has task-specific evaluations | A reproducible separation of state relevance, recoverability, recursive retention and decision value | Complete C01-C05 chain and a meaningful C06 scope test; labels alone are not a contribution |

## 7. Baseline priority after reframing

The minimal discriminating experiment needs: instantaneous observation; short-history classical observer; full-history correctly specified observer; a recursively updated representation; and a true-state reference under the **same** action set and downstream controller. Add an uncertainty-aware belief observer when ambiguity remains after available history. The true-state comparison measures potential value inside this action/controller class, not an absolute optimum over every possible policy.

Next, add a compact LSTM/GRU predictor with matched observations/supervision and explicit memory accounting. A RoboPack-style estimator/predictor separation is the closest structural adaptation when object geometry/touch is central. An AdaptiGraph-style context baseline isolates fixed unknown parameters. RME-inspired VI is justified only if the likelihood and uncertainty target are explicit. PANN/RNO methods enter the carrier-law/observer comparison when constitutive mismatch is demonstrated; they are not automatically required as enormous implementation projects before the hidden-state question is established.

Do not begin with five expensive full-paper reproductions or a VLA stack. First establish a nontrivial action-class opportunity using the true-state reference, and whether available history can realize it. Then reproduce the nearest method that addresses the remaining gap. If a short-window classical observer succeeds, that is a valuable answer about sufficient information, and a reason to stop the unnecessary learned-method claim.

## 8. Inspection provenance and remaining minimum actions

New source excerpts are archived as text under `../../../Documents/Codex/2026-10-25-hidden-state-reframing/literature/`; `literature_registry.json` records URLs, revisions, inspected pages, and access limits. Full PDFs and rendered checks remain in the original 2026-10-23 archive.

Minimum unresolved actions: obtain one accessible P01 sample or use P02's smallest relevant sample to verify a selected baseline's original interface; measure real sensor timing before choosing an observer window; obtain actual robot access/control-mode confirmation; and run a small shared-controller true-state versus short-history comparison before scaling robot training. These actions obtain specific missing evidence. None requires replacing the hidden-state theme with generic deformable-object modeling.

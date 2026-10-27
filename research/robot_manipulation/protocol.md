# Reproducible staged experiment protocol

Version 0.1, 2026-10-23. **Design only.** Proposed numbers below are planning defaults. Physics calibration, independent pilot data, and measured throughput must resolve designated open values before a versioned confirmatory freeze. No results, simulator qualification, or real-material validation are claimed.

## 1. Research questions and scope

The primary robotics question is whether estimating residual material memory improves constraint-respecting task completion beyond strong classical estimation and ordinary feedback. The secondary questions concern prediction, reuse across future controls, and the regimes where a representation adds no value. The broad algorithmic novelty claim is rejected in [novelty_decision.md](novelty_decision.md).

Use recoverable, nonadhesive viscoelastic solids first. Exclude fracture, plasticity, Mullins damage, adhesive pull-off, poroelastic drainage, and temperature drift from the initial claim. They can be separate model-mismatch conditions only after an appropriate plant is verified. Exceeding a strain threshold is a deformation-bound violation, not automatically physical damage.

Separate four uncertainties rather than hiding them in a single latent:

- A: residual material state under fixed material parameters, shape, and contact law;
- B: unknown static parameters, including relaxation constants and friction;
- C: model structure, such as additional relaxation modes or finite-strain response;
- D: observation uncertainty, biases, occlusion, and timing.

A is the primary mechanism experiment. B-D are separately labeled robustness experiments. Geometry must not be silently changed when demonstrating A.

## 2. Stage gates

| Stage | Required experiment | Exit evidence | Stop or revise condition |
| --- | --- | --- | --- |
| S0: constitutive/contact verification | Analytic relaxation and creep, elastic limit, mesh/time refinement, work balance | Reproducible verification report with numerical error budget | Numerical/contact error is comparable to the claimed history effect |
| S1: spatial 2D mechanism | Plane-strain mesh, free lateral surfaces, rounded tool, measured side displacement; matched histories | Observable state difference under common future commands, plus classical and local-history comparisons | Full observation matching removes the effect, or ordinary estimation explains it completely |
| S2: 3D robot qualification | Dynamically simulated seven-joint arm, gripper, 3D material, bidirectional reaction forces, causal sensing | Joint/contact/energy checks, measured latency, stable execution of both tasks | Tool teleportation, unverified coupling, infeasible sensor interface, or unbounded numerical drift |
| S3: confirmatory 3D manipulation | Two closed-loop tasks, frozen protocol, strong baselines, independent held-out blocks | Effect sizes, uncertainty, failures, videos, replay package, null regimes | No useful action gain under credible common feedback; or gain disappears with fair comparison |
| S4: physical robot | Material-bench calibration, independent specimens, robot calibration and task replication | Sim-to-real discrepancy and real task evidence under the same interfaces | Simulated material behavior fails bench validation or the robot action benefit does not transfer |

S2-S3 are mandatory before physical robot manipulation. Material coupon measurements may occur earlier to calibrate the simulation; without them the environment is a physically consistent synthetic plant, not a validated digital twin. Passing S1 does not justify skipping the full robot study.

## 3. Models, observables, and causality

Let the plant state contain robot configuration/velocity, deformable geometry/velocity, and internal material fields. Material parameters are constant within a trial; residual internal fields evolve through loading, rest, and recontact. A conceptual model is:

`x_dot = f_theta(x, u), o_t = h(x_t) + sensor_noise, z_t = E(o_past, u_past, timestamps)`.

The prediction interface is `predict(z_t, observed_robot_state, future_command_plan, controller_config)`. It predicts future realized motion, force, and deformation. Future measured indentation, future force, future images, or test-only material fields are forbidden inputs. A robot command is not the realized force or displacement.

Shared deployable observations are robot joint position/velocity, issued commands, available joint effort, wrist wrench, gripper position and jaw force or motor-current estimate, and RGB-D/side-marker measurements with acquisition and delivery timestamps. Wrist wrench alone cannot measure equal-and-opposite jaw squeezing forces. Either supply a credible jaw sensor/current channel to every method or redesign the grasp task. Shared preprocessing and sensor calibration must be fixed before comparison.

Only the evaluator and explicitly marked oracle may inspect internal stresses, material memory variables, exact parameters, and full unoccluded geometry. An estimator trained with privileged field labels must be separately labeled; the main candidate and matched data-driven baselines use the same supervision budget. Ground-truth fields may score deformation constraints without being available to the controller.

## 4. Physics and simulator qualification

### 4.1 Backend choice

The reference embodiment is a virtual Franka Panda-style seven-DoF arm with an actuated parallel gripper. This does not assume the user owns that hardware. Use verified inertial properties, joint limits, motor/torque limits, collision geometry, and an explicit controller. Record the source/license and commit of the robot asset.

The preferred feasibility trial is an articulated rigid-body engine coupled to a finite-element material solver: MuJoCo for robot dynamics and SOFA/SofaViscoElastic for the material. The sources establish the components, **not a tested integrated bridge**: [MuJoCo computation](https://mujoco.readthedocs.io/en/stable/computation/) and [SofaViscoElastic](https://github.com/SofaDefrost/SofaViscoElastic). The latter documents linear and finite-strain viscoelastic material options, with time-step sensitivity. Pin compatible revisions only after a build and qualification run.

At each synchronization step, send tool/link transforms and velocities to the deformable solver; return the integrated contact wrench at the same reference frame and time; apply it through the robot Jacobian. Include torque from each contact lever arm. Use substeps or coupling iterations and verify convergence. Disable duplicate robot-material contacts in the rigid engine: otherwise the same contact force is counted twice. Preserve rigid-rigid table/self-collision handling separately.

[SoftMAC](https://minliu01.github.io/SoftMAC/) is an alternative coupling reference with an existing articulated/soft two-way design. Its documented material set does not establish our required relaxation law. If used, add and verify a viscoelastic constitutive model before collecting data. Do not switch backends after test results merely because one gives a larger method gap.

### 4.2 Material family and numerical checks

Start with one- and two-mode standard-linear-solid/generalized-Maxwell response and an equilibrium elastic branch. For strains outside the verified small-strain range, use a finite-strain viscoelastic formulation. A proposed synthetic relaxation-time envelope is 0.05-5 s; actual modulus, density, friction, compressibility, and strain limits must be specified from bench calibration or an explicitly synthetic configuration. Extra modes require verified implementation, not an assumption that a plugin already supports them.

Qualification suite:

1. Single-element stress relaxation and creep agree with analytic references; unloading/reloading and zero-load recovery behave correctly. Elastic controls have no constitutive relaxation state. Disable arbitrary Rayleigh damping initially so numerical damping does not masquerade as material memory.
2. Under zero external work, stored energy plus physical dissipation is consistent with the constitutive law. Test rotating the sample and tool together for objectivity. Check force and torque balance between the robot and material.
3. Refine spatial resolution and time step independently twice. Proposed relative tolerance is 2% for peak force, relevant side displacement, and integrated contact work. Numerical uncertainty must also be below one fifth of the smallest claimed method effect. Near-zero denominators require absolute tolerances fixed from sensor resolution.
4. Initial material step size is at most `tau_min / 100`, tightened if convergence demands it. This is a starting recommendation, not proof of stability. Record robot and material substeps independently.
5. Verify separation, frictional stick/slip, and absence of tensile normal forces in the nonadhesive contact model. Use the selected contact formulation's own residual/regularization tests; do not demand exact hard-contact complementarity from a deliberately compliant model. Proposed penetration tolerance is 0.1 mm for nominal objects, with a refinement study showing force is not dominated by the penalty setting.
6. Quantify energy introduced by coupling and timestamp mismatch using a passive release test. Proposed accumulated spurious-work tolerance is 1% of reference loading work and below the decision-effect error budget. If explicit coupling fails, reduce step size or use converged implicit/iterated coupling before training.
7. Repeat selected evaluation conditions on a finer mesh and a different qualified integration setting. A constitutive-family holdout must change the law, not just the random seed. At least one independent implementation or analytic reduced case checks for shared simulator/model bugs.

Do not treat visual realism as the physics acceptance test. Rendered sensors need credible geometry, calibration, occlusion, noise, and latency; photorealistic textures are secondary unless an image-based representation demonstrably depends on them.

## 5. Spatial 2D mechanism experiment

Retain the existing [2D plan](../2d_contact/README.md): fixed-bottom plane-strain specimen, free sides, rounded normal-contact tool, and at least two lateral observations. Compare elastic and recoverable viscoelastic response under press/hold/release/wait/recontact sequences. Force is computed from the interaction, not prescribed as a ground-truth input to the estimator.

Construct each pair by replaying two loading histories from a physically relaxed condition. At the decision cut, match every declared current observation: robot/tool position and velocity, force, command, contact status, and visible lateral/surface deformation. Use calibration-derived noise tolerances; also show matching residuals. Matching only a scalar indentation and force is insufficient once a camera is available.

Generate candidates with a fixed, seeded rule using only past/current observations. Do not select test pairs by future response, candidate failure, or oracle action disagreement. Report attempted pairs, acceptance fraction, and the full distribution of future effects, including negligible effects. If the effect is below numerical/sensor resolution, call it unidentifiable in that setting.

Proposed S1 sizes are 384 training, 96 validation, and 128 test history-pair blocks, consistent with the existing plan. Separate whole blocks before deriving windows or future branches. The same physical initial state can be replayed under several future commands, but those branches remain one statistical block. Ground-truth internal states cannot be manually edited to manufacture history differences.

The mechanism metric is paired-effect prediction error over the first 1.2 s after recontact. For each block and common command, let `d = force_A - force_B` and `d_hat = predicted_force_A - predicted_force_B`. Compute the root ratio of summed squared errors to summed squared true effects across blocks. Report raw force RMSE, effect magnitude, and side-displacement error as well; do not discard small-effect blocks to improve the ratio.

Compare history versus snapshot with identical capacity, evolution law, and planner. Separately compare fixed versus learned evolution laws under a common encoder. The decisive strong controls are a fitted correct-family classical observer and a short-window observer. A snapshot win alone passes no neural-novelty gate.

## 6. Full 3D articulated-robot tasks

### T1: constrained contact traversal over a recoverable pad

A seven-DoF arm holds a rounded rigid wiping tool and executes approach, contact establishment, a two-segment lateral path with a direction change, lift, recontact, and completion. Use a nominal 100 x 80 x 20 mm pad with free lateral surfaces and a fixed base. The nominal tool radius is 8 mm. Vary permitted pad geometry, relaxation spectrum, friction, path orientation, and preloading history according to frozen splits.

The task objective is coverage of a designated path corridor under a specified normal-force band, not a claim of physically simulating dirt removal. Proposed success: at least 90% of the target path length traversed within a 2 mm corridor while in the force band, final retreat completed within a 15 s post-cut task deadline, and no constraint violation. The task must include motion in 3D, articulated joint dynamics, and contact reaction; an end-effector trajectory simply imposed on the material does not qualify.

Use a force ceiling `F_cap` and force target band `[0.4, 0.7] * F_cap`. For a synthetic study, set and publish `F_cap` in newtons after the independent feasibility pilot. For a calibrated material, derive it from a separate force/deformation calibration, then freeze it across methods. A proposed maximum local principal compressive strain is 0.35; this is an engineering constraint, not a validated damage threshold. Report force-band occupancy, coverage, peak force, strain, time, and contact loss separately.

### T2: grasp, lift, transport, and place a recoverable block

Use the same arm with parallel jaws to grasp a nominal 60 x 40 x 30 mm viscoelastic block, lift it 100 mm, transport it 200 mm, and place it in a target region. Include realistic mass/gravity, friction, finger geometry, gripper actuator dynamics, and slip. Loading history may alter residual material response; do not alter the object's static parameters to create the nominal state-memory contrast.

Proposed success: lift and transport without dropping, then achieve final position error at most 5 mm and orientation error at most 5 degrees within a 15 s post-cut task deadline, with compliant-force/deformation constraints respected throughout. The jaw-force ceiling and the same proposed 0.35 compression-strain bound are frozen from calibration/pilot. The object must retain a feasible grasp-force interval; impossibility caused by excessive weight or too little friction is an explicit infeasible stratum, not an estimator failure disguised as learning difficulty.

Track slip distance, drop events, per-jaw force, maximum deformation, placement error, and completion time. Wrist force alone is not sufficient for the squeezing constraint. No hidden ground-truth slip or stress is supplied to a learned controller unless every deployable comparator gets an equally realizable measurement.

### Common execution conditions

Define the finite-strain compression score at each material quadrature point as `max(0, 1 - min_singular_value(F))`, where `F` is the deformation gradient; take the maximum over points and simulation steps. Thus 0.35 means a minimum principal stretch of 0.65, not an unspecified Green or logarithmic strain. Use unfiltered physical contact force for evaluator constraint checks and the declared filtered measurements for controllers. Count any bound violation at the qualified physical time resolution; separately report duration and integrated excess. A post-cut timeout is task failure. The preconditioning duration is additionally included in whole-episode cost and safety accounting.

Robot servo target is 1 kHz, planner target 20 Hz, RGB-D target 30 Hz, and wrench/jaw sensing target 1 kHz before filtering. These are proposed interfaces to qualify, not measured achievements. Record actual processing rates and end-to-end P50/P95/P99 latency on the evaluation hardware. A method missing its deadline continues with the common last-command/fallback rule; simulation time does not pause to grant free computation.

All methods receive the same available feedback and the same force/deformation fallback. Use a common candidate-action library and low-level controller for estimator comparisons. A reference library can have 27 combinations of three normal/jaw-force offsets, three stiffness scales, and three traversal/transport-speed scales; freeze physical values on validation data. Prediction horizon is initially 1 s and replanning occurs after the first command interval. Optimize or sample the same number of candidates under the same measured time budget.

Include zero added delay as a reference and 20/50/100 ms added delay as a prespecified sensitivity sweep. The primary condition is the measured pipeline delay, not the post-hoc delay that maximizes an effect. Include ordinary fast feedback, elastic-material controls, and naturally distributed histories even if these eliminate the advantage.

Count constraints from the start of the physical episode, including preconditioning, probes, release, approach, recontact, and final retreat. Report task time after the decision cut and total elapsed time separately. Material state is not reset merely because measured contact force reaches zero. Reset requires a declared rest criterion and its measured residual, or a fully saved physical state replay.

## 7. Comparisons and fair adaptation

| ID | Comparator | Purpose and controls |
| --- | --- | --- |
| B0 | Tuned reactive impedance/force controller | Practical performance floor; same sensors, constraints, and feasible actuators; tune fairly on validation |
| B1 | Classical constitutive observer: fitted generalized Maxwell/SLS with EKF, UKF, or moving-horizon estimation | Strong correct-family state inference; same calibration data, full causal history, and common planner |
| B2 | Context-conditioned command-prediction LSTM | Learned sequence baseline informed by P05/P08/P09; joint future motion/force prediction without future measured displacement |
| B3 | Finite-history operator/temporal model | HANO-inspired adaptation with the same boundary observations and command interface; retain its temporal inputs |
| B4 | Tactile latent-physics graph model | RoboPack-style estimation and rollout, including its frozen rollout latent; same observations and planner |
| B5 | Static-property adaptive graph model | AdaptiGraph-style property fitting, temporal features, and equal interaction budget |
| B6 | Learned constitutive-potential model plus boundary observer | PANN/GSM-inspired material law; same boundary observation access, with field-supervised variants marked privileged |
| C | Candidate evolving material-state model | Mechanism under investigation; architecture fixed only after S1 identifies an unresolved deficiency |
| O | Privileged-state oracle | Ceiling using true state/parameters; same actuation, sensor timing of the controller, constraints, and candidate actions |

These are planned adaptations, not implementations completed in this audit. Verify authors' released code, record exact commits, and publish deviations. Do not call an adaptation a faithful reproduction until its original-task check passes or the limitation is explicit. Original constitutive methods consume strain/stress fields; original robot methods have different sensors and objectives. Those interfaces cannot be silently mixed into a table.

The classical baseline must include a full-history version and a local-window version; do not intentionally restrict it to make a long-history network win. Compare linear relaxation (L), nonlinear elasticity without memory (S), quasi-linear viscoelasticity (Q), and state-dependent-rate laws (R) as a separate model-class ladder. Only add R when the simpler classes leave a documented mismatch.

Use HIRE as a mandatory conceptual and ordered-history/fast-feedback control comparison. A resource-intensive full VLA reproduction is required only if the submission claims a new general manipulation policy or superiority to such policies. In the scoped estimator study, add a compact history-conditioned fast-feedback policy with matched data and explicitly label it as an adapted control architecture, not HIRE itself. It is a secondary experiment outside the base workload estimate.

Main ablations: snapshot versus history with equal capacity; history lengths 0.2/0.5/1/3 s; latent dimensions 2/4/8/16 with parameter-matched alternatives; fixed versus learned evolution; context-only versus evolving state; ordered versus shuffled history; state initialization erased after a controlled feedback interval; no uncertainty/fallback; elastic limit; and matched extra-compute controls. Prioritize prespecified causal ablations rather than an unbounded architecture search.

## 8. Data splits and leakage prevention

An independent block contains a material parameter draw, geometry, task instance, and physically realized history or history pair. Every time window, future branch, camera view, sensor-noise replicate, and algorithm replay derived from that block stays together. If multiple blocks share a specimen/material realization or history-generation seed, cluster at that higher level and split it as a group.

For 3D planning, allocate 1,024 training and 128 validation blocks across the two tasks, plus an independent 32-block feasibility/variance pilot. The provisional final test contains 320 blocks per task, 640 total. Within each task, allocate 80 blocks to each of four prespecified strata: in-distribution; history-duration/amplitude OOD; material-parameter-band OOD; and future-controller/speed OOD. Keep all numerical bounds in the frozen configuration. Simultaneous geometry and constitutive-family shifts are additional stress tests, not silently mixed into the primary population.

Half of each test stratum is proposed for a matched-history mechanism population and half for naturally sampled histories. Thus the 640-block plan includes 320 matched-history blocks (two histories each) and 320 natural-history blocks (one each). Report the populations separately. The primary robotics estimand is the natural-history population, equally weighted across tasks and strata; the matched population is a controlled mechanism test. A gain restricted to selected matched pairs does not establish ordinary task utility.

This provisional allocation is not automatically powered for every subpopulation. Re-estimate final size from the independent pilot and the chosen useful-effect target before opening the test set. All normalizers, material fitting, architecture selection, action-library tuning, and baseline selection use training/validation only. Hash the split manifest before final evaluation. Log rejected candidate matches without conditioning on future outcome.

## 9. Metrics, statistics, and falsification

Primary metric: natural-history **constraint-respecting task-completion rate**, averaged with equal weight across the two tasks and four test strata. A trial succeeds only if all task conditions and all episode-wide force, deformation, joint, and collision constraints pass. Report each task and stratum as well. Secondary primary-mechanism evidence comes from the matched-history population, not from pooling it into natural task performance.

Select the strongest deployable baseline on validation data before unblinding the test. Compare C to that baseline as the single confirmatory contrast. Other pairwise comparisons are secondary and use Holm adjustment within their declared family. A proposed minimum useful gain is 8 percentage points; advance only if the point estimate reaches that target and the 95% confidence interval excludes zero, with no material deterioration hidden in an individual task. Also require the upper confidence limit for added constraint-violation risk to be below a proposed 2 percentage-point margin. If the safety margin is not estimable at available sample size, report the result as unresolved.

Use seeds 11, 23, 47, 71, 101 for final learned-model training. Five seeds are not five independent replications of every material block. Estimate differences with paired block outcomes and a hierarchical/crossed bootstrap over independent material/task blocks and training seeds, preserving pair members and branches. Resample within task/stratum while retaining the declared population weights; if blocks reuse the same material realization, resample that realization first. Use 20,000 bootstrap replicates with aggregation seed 1007. For trained-versus-deterministic comparison, average or explicitly model seed variation rather than duplicating the deterministic observations. Report all seed results and sensitivity of the interval with only five training seeds. When binary outcomes have zero discordant pairs or a degenerate bootstrap interval, also report discordance counts and conservative exact paired-binary bounds; a bootstrap interval of [0, 0] must not be presented as proof of population equivalence. Derive the exact bound at the independent-block level, not from frames or repeated branches.

The planning formula in `tools/plan_power.py` approximates a paired binary comparison using discordance probability `d`, difference `delta`, and normal quantiles. At `d=0.25`, an 8-point effect requires roughly 307 independent units for a two-sided 5% test with 80% power; a 5-point effect requires roughly 785. These are planning approximations, not a substitute for pilot-based power under the actual cluster and seed structure. With the proposed split only 320 natural-history blocks enter the primary estimand. Per-task/stratum conclusions are less precise. Do not multiply sample size by frames, history members, branches, or training seeds.

Secondary metrics:

- Force and side/surface displacement RMSE, paired-effect NRMSE, calibration/coverage of uncertainty, and multi-step rollout error.
- Constraint frequency, peak overshoot, integrated excess, slip/drop, completion time, and fallback/defer rate. Report unconditional completion cost with a fixed failure penalty as well as conditional time, so failures are not excluded to improve speed.
- Action regret relative to a fixed-library oracle, evaluated through independent physical rollouts from the same saved state. Define regret as oracle feasible task utility minus the chosen action's utility; report cases where no action is feasible separately. Privileged oracle information never enters deployment.
- State reuse across future controller gains, speeds, and task phases without re-encoding future observations. Subsequent online updates must remain causal and be equally available to comparators.
- Time until common feedback removes predictive or action disagreement, compared with when an irreversible decision or constraint boundary occurs. This is an operational diagnostic, not a new theorem or a universal sufficiency ratio.
- Actual inference/planning time, memory, simulator throughput, and missed-deadline fraction on specified hardware.

Preregister the following outcomes that would falsify or narrow the project claim: no identifiable history effect after complete observation matching; no useful gain against B1 or a short-history model; advantage only on curated pairs; advantage only with unrealistic delay; advantage attributable to model capacity, future information, or numerical artifacts; or failed cross-family/physical calibration. A non-significant test is not proof of equality. Report a confidence interval relative to the useful-effect margin and call an underpowered result inconclusive.

## 10. Compute, reproducibility, and organization

The base workload includes seven trained families (B2-B6, C, and the parameter-matched snapshot ablation), each with five seeds, plus B0, B1, and O: 38 evaluated method instances. With 320 pair blocks and 320 single-history blocks, this is `38 * (320 * 2 + 320) = 36,480` base evaluation episodes. At 15 s per episode this is 152 simulated hours, excluding preconditioning, training, qualification, latency sweeps, and additional ablations. At real-time factor 0.2 this alone costs 760 worker-hours; eight genuinely independent workers would ideally take 95 wall-hours, before contention. These are assumptions to measure, not available-compute promises.

Proposed resource caps are 8 GPU-hours for feasibility/pilot work, 240 GPU-hours for model training and validation, and 1,000 CPU/solver worker-hours for the base evaluation. They are planning caps, not purchased or consumed resources. Use up to ten equally budgeted validation configurations per learned family, with all attempts logged; if the cap cannot support comparable tuning, reduce the study prospectively rather than selectively under-tune baselines. Do not start the full sweep until measured throughput demonstrates a credible schedule. Additional stress tests need a separate budget.

Keep the implementation in the existing repository, with English names, code, comments, configuration keys, and logs. Do not create a second unrelated project or mix simulation modules into literature downloads. A proposed layout, created only as needed, is:

```text
src/nr/
  interfaces/       # observations, commands, state estimates, units
  physics/          # rigid, deformable, coupling, constitutive laws
  sensors/          # calibration, timestamps, filtering, rendering
  estimators/       # classical observers and learned encoders
  models/           # transition and observation models
  controllers/      # common planner, servo, fallback
  tasks/            # planar contact, traversal, grasp transport
  evaluation/       # constraints, paired metrics, uncertainty
configs/            # versioned stage/task/model/split configurations
scripts/            # qualify, generate, train, evaluate, report
tests/              # physics references, interface contracts, replay checks
data/manifests/     # hashes, split identities, provenance
runs/<run_id>/      # config, checkpoint, logs, results, timing
reports/            # generated tables, failures, videos, gate decisions
plans/              # this protocol and decision history
```

Each run records code commit and dirty diff hash, dependency lock/container digest, solver/plugin revisions, hardware/driver, seed mapping, units, asset and material hashes, complete numerical settings, split version, model checkpoint, timing, and failure codes. Store both commanded and realized robot motion. Log acquisition and delivery time for every observation. Preserve contact/internal-state snapshots needed for deterministic replay; if bitwise determinism is unavailable, state tolerances and demonstrate trajectory-level reproducibility.

Release independent split manifests, training configuration, raw per-block outcomes, aggregation code, all failures, and representative uncut task videos. Include a small public smoke scene and one-command replay instructions once implementation exists. The smoke scene verifies interfaces; it is not the confirmatory experiment. Do not invent working commands before the modules are implemented.

Use separate failure labels for task failure, constraint violation, estimator divergence, missed deadline, and infrastructure failure. An action that drives the qualified plant outside declared valid bounds counts as a failure; a reproducible solver defect invalidates the affected condition and triggers a documented protocol revision before rerunning every comparator. Never silently drop failed seeds or episodes.

Before physical robot trials, collect independently reset material specimens over loads and time scales absent from fitting, validate force and lateral deformation, calibrate sensing/actuation, and then replicate both operations under the same logged interfaces. Hardware sample size and independent specimen count require a separate power and availability assessment; repeated touches on one specimen are not independent material replication.

## 11. Freeze checklist and immediate actions

The next concrete deliverable is an S0/S1 evidence package, followed by an S2 full-robot feasibility package. Before S3, resolve and record: compatible solver revisions; material law and coefficients; geometry and mesh; controller/force/strain limits; sensor noise and measured latency; action-library values; inference deadlines; split bounds and population weights; matched-observation tolerances; baseline adaptations; final power calculation; and a complete preregistration hash.

This audit has written the study contract and source evidence, not performed those experiments. A conference-quality claim requires passing these gates and reporting the negative results as carefully as positive ones.

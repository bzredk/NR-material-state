# Existing evidence, exact state mechanism, and the next discriminator

Audit date: 2026-10-25. Scope: read-only inspection of archived E1/E2/E3 code, configurations, summaries, and array schemas. No training, new physics rollout, or new scientific result was produced for this audit. Status terms: **FACT** is directly supported by the named artifact; **DERIVATION** follows from inspected equations under stated assumptions; **INFERENCE** is an interpretation; **OPEN** requires another test.

Stable evidence IDs used here are SRC-E1 (E1), SRC-E2 (E2), SRC-E3 (E3), MC01 (fast/slow mechanism), and EX00 (the minimal discriminator package spanning X01-X07). Existing experiment paths are relative to the repository root.

## 1. What was actually implemented

| ID | Verified implementation | What it establishes | What it does not establish |
| --- | --- | --- | --- |
| SRC-E1 | One-dimensional unilateral generalized-Maxwell contact, two dashpot-extension states; fixed correct model family fitted on training trajectories; 3 s histories; equal-capacity history/snapshot encoders | Instantaneous position, velocity, total force, and command can alias physically different internal states; past observations predict their different future response | General object-state discovery, necessity of long history, necessity of neural inference, material-family transfer, spatial 2D behavior |
| SRC-E2 | Same history-to-two-state inference, fixed physical evolution, future command and controller gains supplied separately; one encoding reused across future branches | Conditional reuse across tested future controller settings within this known dynamical family | General state sufficiency, recursive learned filtering, cross-carrier or cross-mechanism transfer |
| SRC-E3 | Frozen SRC-E2 encoders initialize one common causal observer and one common receding-horizon controller; shared 0.3 s release and subsequent feedback | The original initialization advantage did not yield useful action benefit in this task and observer | That hidden state is irrelevant to all tasks; that no controller can benefit; that learned state inference is universally unnecessary |

### Source anchors

- SRC-E1 dynamics: [physics.py](../../early%20experiment/experiments/01_history/physics.py), `material_step` line 26, `step` line 38, `ground_history` line 77, `local_contact_observer` line 93.
- SRC-E1 state encoder: [models.py](../../early%20experiment/experiments/01_history/models.py), `StateModel` line 18 and stress/split parameterization lines 29-32.
- SRC-E1 physical history generation: [data.py](../../early%20experiment/experiments/01_history/data.py), lines 10-44; endpoint noise coupling line 68; test history reuse lines 93 and 104.
- SRC-E1 calibration: [experiment.py](../../early%20experiment/experiments/01_history/experiment.py), `fit_material` lines 34-46, and [fixed_material.json](../../early%20experiment/experiments/01_history/runs/round2_v1/fixed_material.json).
- SRC-E2 interfaces and controls: [README.md](../../early%20experiment/experiments/02_transfer/v2/README.md), [models.py](../../early%20experiment/experiments/02_transfer/v2/models.py), and [dynamics.py](../../early%20experiment/experiments/02_transfer/v2/dynamics.py).
- SRC-E3 dynamics: [vendor/round4/physics.py](../../early%20experiment/experiments/03_feedback/vendor/round4/physics.py), `rhs` line 19.
- SRC-E3 observer/planner: [vendor/round4/control.py](../../early%20experiment/experiments/03_feedback/vendor/round4/control.py), observer lines 21-40, candidate selection lines 67-85, episode logic from line 87.
- SRC-E3 common-prefix assimilation and evaluated methods: [bridge.py](../../early%20experiment/experiments/03_feedback/bridge.py), lines 30, 42-50, 106-119, and 190-205.
- SRC-E3 outcome definitions: [analyze.py](../../early%20experiment/experiments/03_feedback/analyze.py), lines 18-57; [config.json](../../early%20experiment/experiments/03_feedback/config.json); [summary.json](../../early%20experiment/experiments/03_feedback/results/summary.json); [report_numbers.json](../../early%20experiment/experiments/03_feedback/results/report_numbers.json).

Line numbers describe the inspected files; paths and named functions remain the stable locator if files are later reformatted.

## 2. MC01: the complete physical model is already Markov

**FACT:** In the continuous E3 model, the state is `s = (x, v, z1, z2)`. Position `x` is measured positive toward the pad; `v` is its velocity; `zi` are dashpot extensions, not neural variables invented by training. Let `kt = k_inf + k1 + k2`, free-surface compression `q = (k1*z1 + k2*z2)/kt`, actual material compression `e = max(x, q)`, and contact force `F = max(kt*x - k1*z1 - k2*z2, 0)`. Then:

```text
x_dot  = v
m*v_dot = K*(u - x) - D*v - F
z1_dot = (e - z1)/tau1
z2_dot = (e - z2)/tau2
```

The ground-truth values are `k_inf=400 N/m`, `k1=900 N/m`, `k2=1300 N/m`, `tau1=0.15 s`, `tau2=1.4 s`, and actuator mass `m=0.35 kg`. The fitted material is close but is obtained from TRAIN position/force data, not directly assigned the truth values. E1/E2 use a backward-Euler discretization of this mechanism; E3 uses RK4 with a finer integration grid. The stored E2 histories are not retrospectively regenerated with the new integrator before E3 starts.

**DERIVATION:** Given the complete state, known physical parameters, and future command/controller schedule, the equations determine the future. The full model is Markov. The observation vector `(x, v, F, u, dt)` is a partial observation of that already-Markov system. A failure of instantaneous prediction is therefore an observation/state-description problem, not evidence that the physical system itself is non-Markovian.

In contact, the two Maxwell-branch force contributions are `fi = ki*(x-zi)`; total force combines both and the equilibrium elastic branch. Observing their sum does not reveal the individual contributions. Two histories can produce the same `x,v,F,u` and different `z1,z2`, with `k1*delta_z1+k2*delta_z2=0`. Different rates then make their future force responses diverge under the same input. Out of contact, material memory is carried and relaxes; zero contact force does not imply a relaxed specimen.

Do not equate the numerical values `tau1,tau2` with the exact free-recovery eigen-times in every regime: the detached free-surface constraint couples the internal variables.

### Command, physical input, and robot state are distinct

`u` is an impedance position reference. The achieved motion `x` and force `F` follow the coupled equations; `u` is neither actual indentation nor prescribed contact force. Future measured `x` or `F` is unavailable at prediction time. During filtering, past/current measured `x` can legitimately drive material-state propagation.

The two object coordinates alone are not the complete robot-object state. Even this 1D model also needs `x,v`, actuator mass, and the command/controller schedule. A real articulated task additionally requires joint positions/velocities, tool and object pose/velocity, actuator state, persistent friction/contact variables when the contact model has them, and explicit controller/filter/command-buffer state when those influence execution. In the present memoryless unilateral normal-contact law, contact status and free surface are derived from the physical state; in richer models they may require additional state. Missing robot variables must not be concealed in an uninterpretable object latent.

## 3. Why a short history can suffice in the current model

**DERIVATION, limited to known parameters, contact, and adequately measured position/force:** In contact, subtract the known elastic term and input-driven part. The unknown internal dynamics have `A=diag(-1/tau1,-1/tau2)` and observation row `C=[k1,k2]`. The two-row observability matrix is:

```text
O = [ k1           k2         ]
    [ -k1/tau1     -k2/tau2   ]
det(O) = k1*k2*(1/tau1 - 1/tau2)
```

It has full rank when both branches are visible and the relaxation times differ. For the discrete E1 observer, `ai=taui/(taui+dt)` and the equivalent determinant is `k1*k2*(a2-a1)`. A noiseless sequence over more than one instant can therefore identify the two states even though one instant cannot. This explains why a well-specified short-window least-squares observer is a serious baseline.

This rank statement does not specify a robust window length. Nearby time constants, weak branch amplitude, measurement noise, inaccurate parameters, sampling, contact loss, and the condition number of the noise-weighted observability Gramian control practical inference. With known linear dynamics, mathematical state observability does not require a special persistent excitation in every case; useful signal-to-noise and simultaneous parameter identification can require richer actions. In detached contact, `F=0` is an inequality and the in-contact equality must not be used. The current observer code explicitly respects that distinction in E3.

**OPEN:** No experiment in SRC-E1-SRC-E3 establishes a universally sufficient 0.2 s window, a need for 3 s history, or minimal state dimension. No residual-history test has shown that older history adds no predictive value conditional on the compressed state and known context. A recurrent network architecture alone provides none of those conclusions.

## 4. SRC-E1: what the classical and short-window comparisons really say

**FACT:** The state network uses current force and position to fix one combination, `r=kt*x-F`; a sigmoid head predicts one fraction and sets `z1=fraction*r/k1`, `z2=(1-fraction)*r/k2` (with a small clamp). The trained problem is one-dimensional split inference inside a prescribed two-state constitutive family, not discovery of an arbitrary object-state ontology. Its supervision is future force/position prediction, not hidden-state labels. Both history and snapshot use the same GRU capacity and physical rollout.

The full-history classical estimator integrates measured position from a **known relaxed start**, using the correctly specified fitted material family. The local observer uses the final **known in-contact 0.2 s** of position and force and estimates the unknown window-start state by least squares. These different initialization assumptions must be exposed. The latter result is especially informative because it does not require the full relaxed-start record.

| Method, SRC-E1 test-wait | Archived force RMSE | Interpretation |
| --- | ---: | --- |
| Full-history classical integration | 0.000234 N | The known calibrated mechanism already explains almost all of this synthetic problem |
| History network | 0.003680 N | Beats snapshot, but not the strong mechanistic baseline |
| 0.2 s classical observer | 0.003695 N | Nearly the same prediction error as the long-history network in this contact regime |
| Snapshot state model | 0.052179 N | Current observation is deliberately ambiguous |

**INFERENCE:** These results constrain a claim of neural necessity and long-history necessity. They do not invalidate hidden-state inference as a research topic. A harder information condition, unknown initial state, or different mechanism may create a legitimate inference problem, but must be introduced and compared explicitly rather than weakening the classical model without explanation.

### Pair construction and split qualifications

**FACT:** Histories are generated by command perturbations and physically replayed from relaxation; internal states are not manually spliced. The construction finds a null space of the endpoint observation Jacobian, then uses the **simulator's hidden-state Jacobian** to favor an alias direction. This is privileged mechanism-oriented experimental design, although it does not select cases by future response. Perturbations are shrunk if needed for current endpoint/contact feasibility; all seeds are retained. The archived E1 quality file reports 2/384 training pairs shrunk, no validation/test pairs shrunk.

The final measurement noise is coupled within each pair so snapshots are byte-identical. That is a controlled synthetic isolation device, not evidence that real independent sensor noise will produce identical readings. New physical/simulated sensor studies should use independently generated noise, match within calibrated resolution, and report acceptance and residuals. Preserve both the controlled-pair experiment and an unbiased natural-history population.

The test-wait range `[0.8,1.2] s` lies between the training bands `[0.2,0.5]` and `[1.8,2.2] s`: it is an interior holdout, not extrapolation. `test_id` and `test_wait` reuse exactly the same history pairs with different future waits. They are not two independent physical test samples. The carrier and material parameters are fixed; the independent sampling units are history-generating seeds conditional on this one material model, not independent material specimens.

## 5. SRC-E2: cross-action reuse, with a bounded interpretation

**FACT:** The encoder receives a 301-by-5 history under fixed past gains, once per test history. Future gains and commands condition the rollout separately. Training uses four gain combinations; testing includes a gain interpolation and stiffness/damping extrapolation. The fixed model has 3,777 trainable encoder parameters; the conditional GRU has 8,001 parameters and predicts a temporal closure rather than using the same internal-state evolution. Thus the latter is not an isolated representation ablation.

The archived held-out prediction errors are approximately 0.0038 N (history), 0.0350 N (snapshot), 0.00048 N (classical integration), and 0.00313 N (local observer). The physical-reference model uses true state and true parameters; ordinary estimators use fitted parameters. For a pure state-information comparison, add a reference with true state but the **same fitted predictor**, and reserve true-state/true-law access as a separate plant-model diagnostic.

The discrete future library consists of fast, slow, very slow, delayed-fast, and shallow presses. Predictive methods share a selector; the original reactive reference has ongoing feedback and a continuous action interface, so its difference is not attributable solely to representation. An exact/no-margin discrete reference only optimizes within that library, horizon, cost, and constraint definition. It is not an upper bound over every possible robot policy.

**INFERENCE:** Reusing an estimate across future gains is useful supporting evidence for decoupling object-state inference from a particular future controller. It remains within one carrier/mechanism and prescribed physical structure. It does not demonstrate online recursive inference by the learned representation: the neural encoder is used at the cut, and the known dynamics/observer handle subsequent evolution.

## 6. SRC-E3: the negative result is real, but its cause is not fully isolated

**FACT:** SRC-E3 freezes six SRC-E2 models, three seeds each for history/snapshot, and uses the first 64 stored pairs without outcome filtering. Every method gets the same 100 Hz observations, 50 Hz action update, 0.3 s release prefix, fitted physical predictor, common observer settings, and receding-horizon controller. The predictive controller searches a fixed rate grid plus the continuous reactive proposal; its predicted tail is a shared reactive policy. The action experiment evaluates classical, six neural initializers, and two reactive controllers. A full-state-reference controller is supported by vendor code but **is not one of the nine archived SRC-E3 action methods**.

Archived history-minus-snapshot safe-success gain is 0 percentage points. The reported completion-cost gain is `-2.8935e-6 s`, below the prespecified useful thresholds of 0.05 s or 2 percentage points. The archived bootstrap interval `[0,0]` for the binary success difference describes a degenerate resampling result; it is not proof of population equivalence. Independent units are the 64 pairs, not the 3,456 branches per method or repeated seeds.

The most important qualification is the observer handoff:

| Seed-11 initializer | State RMSE at original cut | State RMSE after shared release |
| --- | ---: | ---: |
| Classical | 0.000897 mm | 0.025150 mm |
| History | 0.014404 mm | 0.025152 mm |
| Snapshot | 0.165452 mm | 0.025119 mm |

These figures come directly from `results/report_numbers.json`. The common covariance is initially `0.0015^2 I`; the same force-innovation update is then applied. Snapshot improves, while initially more accurate classic/history estimates become less accurate. Convergence therefore cannot be interpreted simply as all methods recovering the true state from additional data. It is consistent with the shared observer's covariance/noise assumptions overwriting initializer differences. Equal observer settings isolate an initializer comparison, but do not establish optimal uncertainty treatment for each initializer. A confidence-calibrated comparison is missing.

All predictive methods reach 100% success **in the post-handoff task window**, creating a ceiling for that success metric. When the preceding prefix is included, 522/3,456 branches already exceed their later assigned force cap; end-to-end success is 84.8958% for each predictive method. The whole-episode constraint must be primary in the next experiment. The saved negative difference is not erased by this correction, but a claim of 100% whole-operation safety would be wrong.

**INFERENCE:** SRC-E3 supports “initial prediction advantage is not sufficient for a useful action advantage in this feedback/task configuration.” It is consistent with feedback replacing earlier information and with task saturation. Because initializer uncertainty is not calibrated and no full-state action reference is evaluated, the data do not isolate those explanations completely. Do not conclude that the task has zero possible state-information headroom or that feedback universally makes history irrelevant.

## 7. EX00: minimal discriminatory design before a broad benchmark

Status: **PROPOSED, NOT EXECUTED**. Reuse the 1D code only as an inexpensive diagnostic harness and archived reference; the new spatial evidence must come from true 2D contact with side measurements. Avoid starting two large 3D tasks before the mechanism and decision tests are informative.

### One hypothesis and one primary operation

Hypothesis: after matching all current deployable observations, past actions/measurements can reduce uncertainty about a response-relevant state, and this reduction affects a feasible action before ordinary feedback supplies equivalent information. Use force/deformation-constrained recontact and hold as the first diagnostic operation; select any finite decision deadline from the intended operation and measured platform timing, not merely to create a neural advantage. A later full 3D implementation can add a meaningful lateral move or insertion step if that is necessary for the actual task and supported by the platform.

### Common information and method set

| Method | Inputs and assumptions | Role |
| --- | --- | --- |
| Instantaneous model | Current deployable observation, command/controller context, same calibration | Is current information insufficient? |
| Short-window classical observer | Recent position/force/side observations; explicitly inferred or known contact; same fitted physics | Is a modest recent window already enough? |
| Full-history classical estimator | All past deployment channels; relaxed-start assumption only when actually supplied | Does known-model inference explain the effect? |
| Full-history learned initializer | Same observations and calibration; no hidden-state labels in the main track | Does learned inference add anything beyond strong physics? |
| Recursive representation | Update carried state/belief using only the latest action and arriving observation, without re-reading the whole past | Can compact state be maintained consistently? |
| True-state reference | Exact hidden state; same fitted predictor, controller, candidate actions, constraints, and budget | Is there state-information headroom under this fixed task/interface? |
| True-state/true-law diagnostic | Additional exact plant parameters/dynamics | Separately diagnose predictor/model mismatch; not an ordinary competitor |

Keep sensor delivery timing, action library, cost, controller, tuning/calibration data, and compute budget fixed. Declare privileged supervision separately. A full-history estimator and a recursive estimator may use different computation schedules; measure the resulting latency rather than pausing the environment for one of them.

### Small sequential test, not a full Cartesian product

1. **Response relevance:** replay physically feasible histories from declared initial conditions, match all instantaneous channels at sensor resolution, and issue the same action. Compare full response distributions and pair-matching residuals; include all generated seeds and report rejected matches. First verify the effect exceeds numerical and sensor error.
2. **Information availability:** use one representative contact/probe policy and compare 0, 0.05, 0.2, 0.5, 1, and 3 s histories, plus the true-state reference. Estimate conditional state/response uncertainty and observability conditioning. Test one low-information action and one physically safe informative action, rather than multiplying every task condition.
3. **Compression and recursion:** at common cuts compare `encode(full history)` with repeated `update(previous representation, action, observation)`. Train an additional predictor with earlier history appended to the representation; persistent held-out improvement falsifies predictive sufficiency at that horizon/action class. No improvement with a weak probe model is inconclusive. Evaluate restart, missing observations, irregular timestamps, and rolling initialization only after the basic update works.
4. **Decision headroom and feedback:** compare the methods under the same natural sensing/feedback loop. Include an immediate-predecision cut and the real operation's delayed decision, with deadlines specified before test access. Analyze when state/response uncertainty decreases relative to the decision becoming irreversible. An added-delay sweep is secondary, not the primary way to manufacture utility.
5. **Observer uncertainty diagnosis:** contrast the archived common-covariance rule with uncertainty calibrated on validation/pilot data for every initializer, and include a no-innovation propagation diagnostic. This separates genuine information gain from indiscriminate overwrite. Do not select covariance using final task outcomes.

Use an independent pilot to select feasible force/strain limits and estimate variance. Freeze final thresholds, action set, observation matching, sample size, and aggregation before a fresh test. Archive old results unchanged. Pilot task selection may inspect task-level feasibility/headroom but final history cases must not be selected by future effect or method outcome.

## 8. Four explanations and the next decision

| Case | Required pattern of evidence | Alternative explanation to exclude | Next action |
| --- | --- | --- | --- |
| 1. State changes physics but the task does not need it | Common-action responses differ, while fixed-interface true-state decisions provide no useful improvement over a competent feedback baseline | Inadequate oracle search, saturated metric, insensitive action library, or poor utility definition | Narrow to a prediction/representation result or choose a justified task; do not force a control claim |
| 2. State is useful but unidentifiable with available sensing/excitation | True-state reference has useful task headroom, yet history-conditioned uncertainty remains large even for correct-model inference | An underfit learner mistaken for an information-theoretic limit | Add a realizable probe/sensor, retain a belief and robust/defer policy, or drop the unattainable point-state claim |
| 3. History identifies state, but ordinary feedback resolves it before the consequential decision | History improves predecision prediction; equal causal feedback yields comparable relevant uncertainty and actions before the decision deadline | Common high covariance merely erases good initialization; task success ceiling | Report the feedback-substitution boundary; do not make fast feedback artificially worse |
| 4. State is useful and identifiable, but current inference wastes information | True-state task headroom remains; strong identifiable-model inference succeeds while the candidate fails, or a justified learned method improves on all adequate baselines | Different data, privileged labels, future-input leakage, weaker classical fit, or extra compute | Improve the specific inference/update mechanism and make that deficiency the method target |

These cases need not be globally exclusive; a dataset can contain several regimes. Classify prespecified groups and show their prevalence. Failure of the neural model alone cannot establish unidentifiability. Success of an oracle under one action library cannot prove global optimality or a universal task boundary.

## 9. Three figures for the next Nadia discussion

### Figure N1: physical aliasing with a complete information contract

Use a prespecified archived E1 pair (for example index 0, without searching for the largest effect). Show both real command histories, matched terminal `x,v,F,u`, the two true branch states/contributions, and the common future command with different force responses. Add the equations above and distinguish simulator-only states from deployment channels. This is archived synthetic evidence, not a real-material demonstration. Do not show lateral deformation until spatial data exist.

Raw sources: `early experiment/experiments/01_history/runs/round2_v1/data/test_wait.npz` has `history [192,2,301,5]`, `commands [192,2,420]`, `truth [192,2,420,3]`, `oracle_z [192,2,2]`, `pair_ids`, `endpoint_mismatch`, and `construction_shrink_count`. `states.npz` and `predictions.npz` include method/seed/split keys. Existing `figures/02_history_pair_and_response.png` and `figures/03_state_recovery_and_exchange.png` can guide the layout; label any state-exchange panel as a representation diagnostic, not a physically generated new history.

### Figure N2: separate prediction benefit, observer overwrite, and action benefit

Three linked panels: (a) E1 force RMSE of classical/full history/local/snapshot; (b) E3 seed-11 state RMSE before and after the common prefix, including the initially accurate classical estimator; (c) E3 cost/success differences, with task-window versus prefix-inclusive success shown explicitly. This figure must expose the negative result and the observation-model caveat together.

Raw sources: SRC-E1 `summary.json`; SRC-E3 `results/report_numbers.json`, `results/summary.json`, and `raw/prepared.npz`. The latter contains `cut_truth [128,4]`, `prefix_truth [128,31,4]`, `cut_<method>`, `prefix_z_<method>`, and handoff covariance. Existing SRC-E3 figures `01_prediction_transfer`, `02_feedback_and_action_change`, and `03_action_outcomes` are archived evidence; their original captions distinguish scope.

### Figure N3: proposed diagnostic decision map

Draw a schematic evidence map with axes “state-information headroom under the fixed task/controller/action set” and “remaining ambiguity at the consequential decision,” with the four cases above and their next actions. Attach the staged measurement chain: current aliasing -> history information -> compression/recursion -> cross-action prediction -> decision utility -> transfer. Label the entire map as **proposed diagnostic framework, not measured data**. Do not draw invented effect-size curves or assign regimes without tests.

The three questions for Nadia are then scientific rather than architecture shopping: which operation has a real decision that may precede feedback resolution; which observation and intervention channels can actually be obtained; and whether the desired contribution is a new inference mechanism or a scoped empirical boundary about sufficient physical understanding.

## 10. Mapping to the shared validation IDs

| Shared ID | Test | Existing support | Smallest missing evidence |
| --- | --- | --- | --- |
| X01 | State relevance beyond current observation | SRC-E1 synthetic matched-current pairs | Spatial 2D replication with all deployed side/surface observations matched |
| X02 | History information and needed excitation/window | SRC-E1 full versus 0.2 s observers | Window/conditioning study with unknown initial state and realistic contact/noise |
| X03 | Residual-history predictive sufficiency | Not tested | Compare prediction from representation/context with and without additional older history using adequately expressive matched probes |
| X04 | Recursive consistency | Known-law observer recursion in SRC-E3; learned state update untested | Compare full-prefix encoding to causal carried-state update under matched cuts and new observations |
| X05 | Cross-action reuse | SRC-E2 controller-gain transfer within one model family | Fresh actions outside the training policy, with the same inferred state and no future measurement inputs |
| X06 | Decision utility | SRC-E3 negative initializer result | Same-predictor true-state reference, calibrated uncertainty, natural feedback, and full-operation constraints |
| X07 | Transfer scope | Future gains only; fixed synthetic carrier | Separate object/geometry, parameter, mechanism, embodiment, and real-material transfer claims |

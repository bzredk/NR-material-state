# State, observation, action, and empirical sufficiency

Status: mathematical definitions and source-grounded interpretation, 2026-10-25. The equations describe the archived synthetic model, not a verified real material. Theoretical sources T01-T04 were read in relevant full-text sections; no universal representation theorem is claimed for this project.

## 1. Factor the system before choosing a representation

| Symbol | Meaning | Examples and epistemic status |
| --- | --- | --- |
| `s_obj,t` | Complete object state relative to a declared physical model | Geometry/deformation, velocity and internal relaxation variables; simulator fields are privileged model truth, not a uniquely established physical ontology |
| `s_robot,t` | Robot/actuator state | Joint positions/velocities, tool pose, actuator lag and gripper dynamics |
| `s_contact,t` | Persistent contact state if the law requires it | Stick/slip displacement, attachment/contact memory; instantaneous contact mode can instead be derived in a memoryless contact law |
| `s_exec,t` | Execution state affecting future dynamics | Servo integrator, sensor filter, command queue and clock/latency state |
| `S_t` | Combined model state | `(s_obj,t, s_robot,t, s_contact,t, s_exec,t)` with redundant variables removed |
| `theta` | Fixed but possibly unknown parameters | Stiffnesses, relaxation constants, mass, sensor calibration; unknown is not synonymous with dynamically evolving |
| `c` | Context | Geometry, boundary condition, tool identity, frame convention, controller type and task specification; if context evolves unpredictably, model its evolution explicitly |
| `u_t` | Issued action command | Reference pose/velocity, impedance setting, force target or torque command, depending on the actual API |
| `a_exec,t` | Achieved physical actuation | Actual actuator force/motion resulting from command, robot state, delays, saturation and contact; not interchangeable with `u_t` |
| `o_t` | Available instantaneous observation | Delivered proprioception, wrench, side shape and command feedback with timestamps; a filtered reading can already contain past information |
| `H_t` | Causal information history | Prior observations, issued commands, actual execution records available by time t, calibration context and initial-state knowledge |
| `z_t` | Inferred representation | A compressed statistic of `H_t`; all retained hidden/cell states and buffers count toward its memory |
| `b_t` | Belief | A conditional distribution over unresolved state, and optionally over separately represented parameter uncertainty |

With a sufficient combined state and a declared disturbance model, write `S_(t+1) ~ p_theta(. | S_t,u_t,c)` and `o_t ~ p_theta(. | S_t,c)`. This is already a Markov physical model. A robot observing only `o_t` generally faces a partially observed system. Adding an RNN changes the estimator architecture; it does not establish that its hidden state is sufficient.

Sensor acquisition time and delivery time differ. The causal history must use only observations that have arrived by the decision, while the state estimator can compensate for their earlier acquisition times. Future actual motion is an output of a command-conditioned prediction, not an allowed input. During filtering, already observed actual motion is legitimate evidence.

## 2. Exact fast/slow mechanism in the current code

SRC-E3 uses `S=(x,v,z1,z2)`, with `zi` physical dashpot extensions. Define `kt=k_inf+k1+k2`, `q=(k1*z1+k2*z2)/kt`, `e=max(x,q)`, and `F=max(kt*x-k1*z1-k2*z2,0)`:

```text
x_dot   = v
m*v_dot = K*(u-x) - D*v - F
zi_dot  = (e-zi)/taui
```

The full state, parameters, controller schedule and future commands determine future motion. In contact, branch forces are `fi=ki*(x-zi)`. Matching `x,v,F,u` only constrains the weighted sum `k1*z1+k2*z2`. For two histories at a common in-contact cut:

```text
k1*delta_z1 + k2*delta_z2 = 0
delta_F_dot = (k1/tau1)*delta_z1 + (k2/tau2)*delta_z2
```

The second expression need not vanish when the time constants differ. Equal current force can therefore conceal different subsequent force evolution. This is a concrete omitted-state mechanism, not evidence that the underlying physics violates the Markov property. In free space, `F=0` supplies an inequality and the material continues recovering; zero force is not a reset certificate. E1/E2 discretize this mechanism differently from E3, as detailed in [existing_evidence.md](existing_evidence.md).

This also distinguishes three explanations: nonlinear instantaneous elasticity alone does not necessarily introduce hidden dynamic state; visible lateral shape may reveal an omitted state rather than establish an invisible one; and model mismatch can arise from an incorrect law, parameter or sensor rather than material memory.

## 3. Structural observability versus practical recoverability

During contact, with known parameters and adequately measured position, subtract the known elastic/input-driven contribution. The internal subsystem has `A=diag(-1/tau1,-1/tau2)` and `C=[k1,k2]`. Its observability determinant is `k1*k2*(1/tau1-1/tau2)`. Distinct visible modes therefore admit recovery from multiple noiseless measurements even though one instant is ambiguous. This is a model-specific derivation using the classical criterion in T01, not a new theorem.

Rank is not an accuracy guarantee. Practical recovery depends on the noise-weighted observability Gramian, time resolution, branch amplitudes, parameter uncertainty and contact availability. Nearly equal decay rates can make inference ill-conditioned. In a known linear system the input's effect can be subtracted, so persistent excitation is not a universal additional requirement for structural state observability. In hybrid contact, unknown-parameter identification and noisy finite observations, action choice can determine whether informative measurements occur and whether the signal is distinguishable.

A finite history window may be sufficient to a tolerance in one operating regime, or insufficient in another. Longer history can preserve slow information but also introduce drift/model mismatch. Choose window length from measured information and error curves, not a preference for large models. The existing 0.2 s result is a conditional observation, not a general bound.

## 4. Three targets and the recommended ordering

| Target | What success means | Advantage | Limit and role here |
| --- | --- | --- | --- |
| A: physically interpretable internal variables | Estimate the declared physical coordinates, with units and uncertainty, under an identifiable model | Diagnostic transparency; analytic observers and controlled truth reference | Coordinate meaning depends on model/parameters. Current code is mainly A: a network infers a scalar split within a prescribed two-state family. Keep A as the instrumented reference |
| B: predictive state | Retain what is needed to predict relevant future response distributions under the declared actions and horizon | Allows different representations and carriers without requiring identical physical coordinates | Empirical adequacy is scoped. **Use B as the main research target**, with explicit C03-C05 tests |
| C: probability belief | Track unresolved alternatives and update their probabilities consistently | Can represent ambiguity and support bounded probing, robust action or defer | Requires an observation/transition model or learned calibrated approximation; a mean/covariance need not capture multimodality. Introduce when ambiguity is demonstrably decision-relevant |

B does not require discovering a novel canonical PSR algorithm. A PSR-inspired future-response representation is one candidate. A physically structured observer may already satisfy B in the first carrier. C can be a distribution over A coordinates or a predictive distribution associated with B; it is not necessarily a separate competing architecture.

For a known model, the Bayes belief update is proportional to the observation likelihood times the previous belief propagated through dynamics. Exact belief is sufficient under the assumed POMDP model (T02); a misspecified Gaussian filter is not automatically sufficient or calibrated. An unknown fixed `theta` can be added to the posterior with identity evolution, while being reported separately from the physical dynamic state.

## 5. Define the claim before testing it

For a declared population `D`, action class `A`, horizon `h`, output vector `Y` and explicit retained variables `r_t,c`, the predictive goal is below. Here `r_t` includes needed robot, contact, execution/filter/queue state or their uncertainty; it is not just a robot pose. Context `c` has the meaning in Section 1.

```text
P(Y_(t+1:t+h) | H_t, do(U), c)
    approximately equals
P(Y_(t+1:t+h) | z_t, r_t, do(U), c), for U in A and histories in D.
```

Here `Y` includes the force, motion, deformation and task/constraint variables actually relevant to the claim. The `do(U)` notation denotes specified physical interventions in controlled experiments; it does not claim discovery of a causal graph from passive sequences. For a feedback policy, simulate its causal observation/action loop rather than conditioning on a future action sequence that already leaks the future observations that selected it.

Representation sufficiency is stronger than low error under one policy. Test whether older history adds held-out predictive information beyond `z_t,r_t,c`, using adequate, capacity-controlled residual predictors and more than one future action. A nonsignificant difference alone is inconclusive. An effect-size confidence interval can bound residual predictive value within the tested scope only when probe adequacy and precision are demonstrated. It does not prove conditional independence or universal minimality.

Recursive consistency means the carried update `z_(t+1)=U(z_t,u_t,o_(t+1),timestamps,c)` preserves the relevant predictions of a full-history estimator at common cuts. Both predictions must also be accurate and calibrated against held-out outcomes; agreement between two wrong models is insufficient. Compare output distributions using proper predictive scores as well as action rankings; RMSE alone restricts the test to conditional means. Arbitrary invertible latent rotations make raw coordinate equality an inappropriate general metric. Inspect all memory. For example, P01's public implementation retains LSTM h/c in addition to its emitted physics vector; the latter alone is not its complete recursive state.

Decision adequacy is narrower in another direction: a representation can omit physically real distinctions that do not change the feasible action choice or utility for this task. Conversely, a small force error can change a threshold-constrained action. Measure action ranking and realized outcomes directly. The true-state reference is restricted to the tested controller, predictor, action library and horizon, and may itself be suboptimal. It is not an absolute upper bound over all robot policies.

## 6. Targeted theoretical foundations

| ID and source | Original scope and verified method | Consequence for this project | Reading/access boundary |
| --- | --- | --- | --- |
| T01: [Stanford EE363, Observability and State Estimation](https://ee363.stanford.edu/lectures/011_observ.pdf) | Known linear dynamics/input-output relations; observability rank and observer construction | Separate one-time aliasing, structural recoverability and numerical conditioning; derive the current two-mode example explicitly | Official course source, not a new research paper. PDF pp. 3-13 inspected; no nonlinear guarantee inferred |
| T02: [Kaelbling, Littman, Cassandra, 1998](https://people.csail.mit.edu/lpk/papers/aij98-pomdp.pdf) | Belief-state filtering and planning for a specified POMDP; the full posterior summarizes history | Motivation for C and for splitting estimator from policy; a most-likely point state is not generally enough | PDF pp. 8-11 inspected, Sec. 3.2-3.4 and policy-tree setup; not all planning algorithms rederived |
| T03: [Littman, Sutton, Singh, Predictive Representations of State](https://proceedings.neurips.cc/paper/2001/file/1e4d36177d71bbb3558e43af9577d70e-Paper.pdf) | State as predictions of action-observation tests; recursive update; finite-POMDP linear-PSR existence result | B and action-conditioned prediction have established foundations; finite windows are not universally sufficient | PDF pp. 1,3,5,7 inspected; scanned file contains intervening blank pages. Theoretical finite discrete setting does not certify a continuous learned robot representation |
| T04: [Givan, Dean, Greig, Equivalence Notions and Model Minimization in MDPs](https://cs.brown.edu/people/tdean/publications/archive/GivanetalAIJ-03.pdf) | Stochastic bisimulation preserves rewards and transition probabilities over equivalence classes; quotient policies preserve optimality under its assumptions | Distinguish preserving physical predictions from preserving task decisions; equal one-step error is not the same guarantee | PDF pp. 11-15 inspected; full appendix proofs not audited. Exact finite-MDP result is a reference, not a claim proved here |

Li, Walsh and Littman's 2006 state-abstraction paper was verified on the author's publication list, but an attempted full-text mirror download returned HTTP 429. Its detailed taxonomy is not used as if deeply read; T04 supplies the directly inspected abstraction argument. Primary source PDFs, hashes and the failed-access record are archived under `../../../Documents/Codex/2026-10-25-hidden-state-reframing/`.

The literature system is therefore A: T01-T04 theory; B: P01/P02/P03/P16 robot estimation and control; C: P04/P05/P06/P07/P08/P14/P15 carrier modeling; D: the code/data/platform audit and resource register. These lines meet at C01-C06 rather than competing to define the entire project.

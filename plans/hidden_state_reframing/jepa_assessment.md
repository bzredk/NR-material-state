# JEPA as a candidate training objective for hidden object state

Status: advisory assessment and proposed pilot; no training, implementation reproduction, or new physical evidence. This supplements the existing research package without changing its topic or stage gates. Sources were checked through primary full-text method/experiment sections; this is a targeted review, not an exhaustive novelty search.

## Recommendation

JEPA is compatible with target B, predictive state, but is neither a physical state definition nor an automatic solution to partial observability. Keep hidden-object-state inference as the research question and treat JEPA as one candidate representation-learning objective. Current priority is a small controlled objective comparison, not a foundation-model migration or a new JEPA-branded project.

The current low-dimensional force/displacement data already expose the variables that matter to the task. Direct physical-output prediction is an efficient, serious baseline, and the archived calibrated classical observer is stronger still. JEPA becomes more motivated when high-dimensional visual/tactile observations contain substantial irrelevant variation, when physical-state labels are unavailable, or when representations must be reused across sensors/actions. It cannot create information absent from the entire deployed history.

## Distinct design axes

| Axis | Choice and meaning |
| --- | --- |
| Research target | A: physical coordinates; B: sufficient future-response predictions; C: posterior uncertainty. JEPA fits B naturally but does not guarantee any of them. |
| Information | Current observation, short history, or complete causal history. The training objective cannot substitute for unavailable history. |
| Memory architecture | Observer, GRU, causal Transformer, state-space model. A GRU can be trained with a JEPA objective; GRU versus JEPA is not an isolated comparison. |
| Learning target | Pixels, measured physical responses, learned embeddings, or a declared hybrid. This is the primary axis isolated by the proposed pilot. |
| Uncertainty | Point forecast, distribution or belief. A deterministic embedding need not be a single physical-state estimate, but ordinary point-prediction training does not itself supply a calibrated belief. |
| Decision interface | Shared physical-output heads and controller first; latent goal distance is a separate controller choice, not automatically a force/deformation constraint. |

## Targeted prior art and reading limits

**J01: [V-JEPA 2 / V-JEPA 2-AC](https://arxiv.org/html/2506.09985v1), 2025.** Read Sections 2.1, 3.1-3.2 and 4.1-4.2. FACT: a frozen visual encoder feeds an action-conditioned causal predictor; the loss combines teacher forcing and rollout prediction. Training actions are differences of measured end-effector states. The reported robot comparison uses blocking execution; one reported planning configuration takes 16 seconds per action. INFERENCE: it establishes latent robot planning, not readiness for this project's fast contact feedback or commanded-input semantics. No code was executed here.

**J02: [LeWorldModel](https://arxiv.org/html/2603.19312v1), March 2026 preprint version.** Read Section 3, Section 6 limitations and Appendices D/F. FACT: joint embedding prediction plus SIGReg trains encoder/predictor without EMA; the predictor uses observation history. Its reference implementation uses one or three context frames depending on task; planning executes the optimized horizon before replanning. INFERENCE: this is a useful lightweight recipe, but matching its architecture does not establish a recursive sufficient state or preserve our feedback conditions. A large isotropic latent is not automatically suitable for a low-dimensional physical mechanism.

**J03: [Toward Physically Grounded JEPA World Models for Goal-Conditioned Robotic Planning](https://arxiv.org/html/2609.03565v1), September 2026 preprint.** Read Sections II-III, equations 1-7 and Table I. FACT: latent prediction is augmented with inverse dynamics and state alignment; experiments use full simulator physical state for training supervision. Baseline means in Table I are taken from LeWorldModel; its inspected release statement promises code upon acceptance. INFERENCE: adding physical-state supervision to JEPA is already prior art. That information condition differs from our main label-free internal-state inference condition. The paper does not establish recovery of our hidden constitutive state.

**J04: [Adaptive Latent Capacity for World Models](https://arxiv.org/html/2609.32921v1), September 2026 preprint.** Targeted reading: Sections 3.3 and 4.1-4.2; full method/proofs and code not audited. FACT: predictive information is concentrated in latent prefixes; its oscillator example contains an invertible nonlinear observation map of the full four-dimensional state. INFERENCE: compact state recovery is also active prior art, but this example is different from physically distinct states with identical instantaneous observations. This distinction does not prove that the method cannot handle partial observations.

The older PSR/POMDP foundations and P01 RoboPack/P16 HIRE remain relevant: action-history prediction and memory-aware control are not new. Unreported experiments do not imply incapability. The current review does not certify a novel JEPA algorithm.

## What JEPA can and cannot identify here

Let `s_t` be the full physical state, `o_t` the deployed measurement, `u_t` the issued command, `r_t` the explicit robot/contact/execution context, and `theta` fixed parameters. Let `H_t` contain only observations and actions available by time t. Use `b_t` for the inferred carried representation, reserving `y_t` for target embeddings.

```text
b_t = F_phi(b_(t-1), o_t, u_(t-1), timestamps, r_t)
y_(t+k) = E_target(o_(t+k), available_future_sensor_channels)
y_hat_(t+k) = P_psi(b_t, future_commands, r_t, fixed_context)
L_embed = sum_k w_k * distance(y_hat_(t+k), y_(t+k))
```

This is a candidate action-conditioned joint-embedding design, not a named new algorithm. One may use an EMA/stop-gradient target or a non-collapse regularization recipe; these are alternatives to test, not ingredients that must all be stacked. Future measurements are training targets only. Full target-encoder history containing the prediction context can create an easy copy shortcut, so begin with explicitly future response targets and diagnose any overlap. Do not provide achieved future displacement when predicting issued-command consequences.

Three limitations are decisive:

1. **Instantaneous aliasing:** if `o_t(A)=o_t(B)`, a deterministic instantaneous encoder returns the same code. A history-conditioned predictor can still distinguish A and B if earlier observations differ, but its memory is then part of the effective state. Do not call the single-frame code the full state.
2. **Task-relevant information can disappear without total collapse:** a nonconstant target embedding can preserve geometry/appearance yet discard a weak force transient or slow recovery mode. Low embedding loss can then coexist with wrong physical responses. Anti-collapse regularization prevents particular degeneracies; it does not certify preservation of every decision-relevant distinction. This is a model-design inference to test, not an observed failure of every JEPA.
3. **Ambiguity can be irreducible:** if available histories cannot separate physically relevant alternatives, a point target may conceal uncertainty. Add an explicitly evaluated distribution/belief only if that uncertainty affects prediction or decision; JEPA alone supplies no calibrated posterior.

For this carrier, targets should include measured force and relevant deformation over horizons spanning calibrated fast/slow behavior. A future force/deformation head can anchor relevance while avoiding pixel reconstruction. This is an explicitly supervised/self-supervised physical-response hybrid, not pure embedding-only JEPA. Actual simulator internal variables remain privileged labels used only in a separately marked comparison or evaluator.

Do not force every matched history pair apart in latent distance: some genuinely do not differ over relevant futures, and arbitrary latent scale makes separation misleading. Test conditional response preservation instead. Likewise, augmentations must preserve physics: camera changes require coordinate handling; changes to deformation amplitude, velocity, force scale or timing cannot be declared harmless nuisance transformations.

## Fit to the existing two frameworks

JEPA primarily changes the **method** axis of the overall matrix and the **method/target information** portion of the mechanism matrix. It does not replace the high-level question, certify the scenario, make a carrier valid, or upgrade an experiment's claim level. Its initial links are C02-C04/X02-X05; C05/X06 remains a separate decision gate. The same D0/D1/D2/D3 status and resource constraints apply.

| Item | Candidate specification |
| --- | --- |
| Full state | Two-mode internal state plus mechanical state; in 3D the appropriate internal field and joint/contact dynamics |
| Observation | Actual force, actual motion and later calibrated side/surface measurements; sensor availability unchanged across methods |
| Action | Issued command plus controller context; past achieved input only after measurement delivery |
| Context | Geometry, material/parameter estimate, boundary conditions and controller/clock configuration |
| Learned representation | All carried `b_t`, caches and filters; no presumed physical coordinate identity |
| Grounding evidence sought | Controlled future-command interventions, nuisance/sensor transformations preserving the same physics, and held-out physical-parameter/geometry tests; decision evaluation remains separate |

## Smallest useful experiment

Use a 2 x 2 comparison: current-only versus a common causal history encoder, crossed with physical-output prediction versus embedding prediction. Keep the observation channels, training parents, encoder capacity, action conditioning, tuning budget and downstream controller matched. Include the short/full classical observers and true-state/same-fitted-predictor reference from the existing protocol. If dynamics heads cannot be matched, use an encoder-by-predictor factorial and label the remaining differences.

Representation-only audit: freeze each encoder, train the same capacity physical response readout on the same calibration/training data, and score held-out response under new actions. This tests accessible information, not automatically native control performance. System audit: compare causal rollouts with a shared physical task cost/controller, reporting model and compute differences. Never compare each method's raw latent loss as though the target spaces were commensurate.

| Claim | Supporting evidence | Falsifier / next action |
| --- | --- | --- |
| JEPA preserves useful history information | Held-out physical forecasts and older-history residual tests are at least adequate, with improved data efficiency or nuisance robustness over matched direct prediction | Low latent loss but missing response modes: target is inadequate; test a physical-response anchor before claiming a better state |
| JEPA adds something beyond generic recurrence | Gain persists with the same memory architecture, sensor data, tuning and controller | Gain comes entirely from extra history/capacity/labels: retain the simpler explanation and stop the JEPA-specific claim |
| Representation matters for action | True-state reference has headroom and the candidate improves full-operation utility under ordinary feedback | No reference headroom, or feedback supplies equivalent information in time: narrow to prediction; do not weaken feedback |

Start with the archived model only as a code/optimization diagnostic; its privileged pairing and coupled endpoint noise remain caveats. New evidence follows the spatial 2D protocol with feasible current-matched histories, independent noise, a natural-history cohort and grouped splits. Test held-out actions and calibrated time horizons before scaling to full 3D. Full-arm qualification remains mandatory before real manipulation. A second mechanism is needed only for a cross-mechanism claim, not for the first pilot.

Use planning seeds 11/23/47, identical small tuning budgets, and a timing pilot before setting GPU-hour promises. Cap the initial sensor-only feasibility exercise at 8 local compute-hours; a cap is not a guarantee of convergence. Large visual pretraining is excluded. All data sizes, group definitions, failures and final-test separation follow [minimal_experiment.md](minimal_experiment.md). The machine-readable extension is [jepa_eval_spec.json](jepa_eval_spec.json).

## PhD-level positioning and decision

**Problem:** a future-embedding objective may fail to preserve physically weak but decision-relevant hidden-state distinctions under partial observation. **Method:** not established; first test whether causal multimodal histories and physically relevant future targets resolve a demonstrated failure. **Insight:** if supported, identify when perceptually compact prediction is adequate for interaction and when it discards information that a robot must retain.

This is a candidate failure-mode/adequacy study, not a claim that adding a force head or recurrence is novel. From an AI perspective, a stronger paper needs a reusable objective, analysis or reproducible failure boundary beyond one material. From a robotics perspective, it needs a credible closed-loop operation, measured sensing and a benefit that survives strong observers and normal feedback. Neither venue rewards the JEPA label by itself.

Proceed only with a small objective comparison. Keep a classical or direct predictor if it already meets the operational requirement. Escalate JEPA investment when it delivers a distinct robustness, data-efficiency or transfer benefit under matched information and resources. Stop a novelty claim if the closest works cover the same problem, supervision, mechanism and insight; a new carrier or renamed latent is insufficient.

# From hidden-state motivation to a defensible contribution

Date: 2026-10-26. Status: clarification of research claims, not new experimental evidence. Applies `physics-grounded-world-model` and `paper-novelty-design-v1`; reuses the existing source audit rather than restarting the literature search.

## Direct verdict

The observation that an object can contain evolving internal variables is the physical motivation. It is not, by itself, the project's novelty. Nor does instantaneous observation aliasing imply that a long input sequence is necessary. The strongest current candidate is a controlled study of which hidden information can be inferred from feasible interaction histories, retained in an updateable predictive state, and used before ordinary feedback makes it redundant. A distinct new inference method is not established yet.

## Five statements with different evidence requirements

| Statement | Current status | Consequence |
| --- | --- | --- |
| Internal dynamic state changes future response | Established for the prescribed two-mode synthetic carrier; internal-variable physics is prior art | Valid mechanism, not a newly discovered physical principle |
| Current deployed readings can be insufficient | Supported in the archived observation model; new spatial channels and independent noise still need checking | State aliasing is relative to sensors, not an intrinsic invisibility label |
| Historical information can resolve some ambiguity | Supported conditionally by classical and learned estimators | Known state-estimation and predictive-state foundations already cover this general idea |
| A long raw history window is necessary | Not established; the archived 0.2 s observer nearly matches the 3 s network | Do not make long memory the promised method advantage |
| A learned state produces useful robot action benefit | Not established; shared feedback is negative within its implementation and lacks a true-state action-reference batch | Keep prediction, representation and action claims separate |

Use 'instantaneous observations are insufficient' rather than 'the current state is insufficient' when referring to the measured displacement, velocity and total force. The model's full physical state is already Markov. The robot does not directly observe that state. We possess action-observation histories, not measured sequences of the hidden physical state.

## Why slow physics does not require a long observation window

In contact, the existing two-mode law can be expressed using branch forces:

```text
F = k_inf*x + f_fast + f_slow
f_i = k_i*(x-z_i)
f_i_dot = k_i*v - f_i/tau_i
```

For an ideal fixed-indentation hold, v=0, contact remains closed, and parameters are known:

```text
F - k_inf*x = f_fast + f_slow
-F_dot = f_fast/tau_fast + f_slow/tau_slow
```

Distinct time constants make these two equations independent. A short, adequately resolved force segment can therefore provide information about the composition through its slope. This is a special-case observability explanation, not a noise-robust guarantee or a new theorem. Under actual command control, achieved indentation may not be fixed; use the measured motion and coupled robot dynamics instead of assuming v=0.

Noise makes derivatives difficult; close time constants, weak amplitudes, detached contact and uncertain parameters can require more history or better excitation. These are hypotheses to measure. Long physical persistence, long required batch windows, and long effective memory in a recursively updated state are different quantities.

A recursive estimate can retain evidence from an old loading event without rereading that entire sequence at each decision. Conversely, an RNN may fail to preserve it. Neither small dimension nor recurrence proves sufficiency.

## Problem, method and insight

| Layer | Defensible current formulation | What remains missing |
| --- | --- | --- |
| Problem | At fixed object parameters, identify evolving state differences that remain after matching all deployed current measurements and affect specified future interventions | Qualified spatial carrier and sensor matching; practical prevalence beyond privileged mechanism pairs |
| Method | Infer/update an object predictive state from causal commands and observations, comparing classical observers, direct predictors and learned latent alternatives | A specific failure of strong methods and a mechanism that addresses it; JEPA remains a candidate objective |
| Insight | Characterize when history is informative, how much must be retained, and when the retained distinction changes a useful action under ordinary feedback | Reproducible boundaries across declared conditions; not merely a restatement of partial observability or information value |

Potential contributions should be stated conditionally:

1. **Problem/benchmark:** a physically realizable, sensor-matched comparison separates dynamic state from fixed parameters, observable geometry and implementation artifacts. It must expose a scientifically meaningful limitation or boundary beyond an already known textbook example.
2. **Representation/method:** a specific compact update preserves cross-action information that established methods lose under matched data and resources. No such method result is currently demonstrated.
3. **Robotics/insight:** the state-information benefit survives an actual operation's actuation, sensing, constraints and common feedback, with no-benefit regimes explicitly reported. Full articulated 3D qualification precedes real manipulation.

These dimensions cannot substitute for one another: a careful benchmark is not automatically an algorithm contribution; lower prediction error is not action benefit; a new material is not a new hidden-state principle.

## Closest overlap and remaining distinction

Classical observability and observers already infer unmeasured state from input-output history. [Predictive state representations](https://proceedings.neurips.cc/paper/2001/file/1e4d36177d71bbb3558e43af9577d70e-Paper.pdf) already represent state through action-conditioned future predictions. P01 RoboPack and P16 HIRE already use interaction information/history for robot inference or control. P04/P14 establish constitutive internal-variable/memory modeling. Detailed primary readings are retained in [closest_work.md](closest_work.md) and [formalization.md](formalization.md).

The candidate distinction is the jointly tested information, representation and decision boundary in a specified dynamic-state setting, not any of these ingredients alone. It remains a contribution hypothesis. A study that only reproduces known state estimation with a different network/carrier should be positioned as reproduction or an application, not rescued by a novelty slogan. The current neural model estimates a split inside a prescribed two-mode family; it has not autonomously discovered the existence or number of hidden physical variables.

## Three falsifiable propositions and next decisions

| Proposition | Test | Result requiring revision |
| --- | --- | --- |
| H1: history contains relevant information beyond current sensing | C01/C02, X01/X02: physically replayed histories, matched current channels, common future commands and independent noise | New visible geometry explains the effect, or history has no useful incremental information within the tested regime |
| H2: a proposed state retains and updates the useful information | C03/C04, X03-X05: residual older-history probe, recursive predictions scored against truth, held-out actions | Older history still materially improves predictions; or the short classical state already meets the same adequacy requirement |
| H3: the information changes a useful robot decision | C05, X06: shared predictor/controller/actions/feedback, true-state reference, complete operation constraints | No fixed-interface reference headroom after sensitivity checks; or common feedback resolves the distinction before consequential action |

H1 alone supports a scoped hidden-state phenomenon. H2 can support representation adequacy within tested conditions. H3 supports the action-value claim. Failure at H3 does not erase H1, but does prevent claiming a useful control method in that regime. Failure to reject a difference is not equivalence.

Use the existing minimal protocol rather than adding experiments solely to justify long histories. Prioritize history-length/excitation curves, adequate short classical baselines, a true-state action reference, and physically credible 2D validation. Do not deliberately degrade sensors, feedback or classical information to create a neural advantage.

## Suggested research wording

One sentence: We study which hidden object-state information interaction histories must retain to predict new actions and support decisions under partial sensing and ordinary feedback.

One paragraph: We investigate robot inference of evolving object state that is not determined by current deployed observations. Using controlled, physically realizable histories, we test whether this information can be identified, compressed and recursively updated for prediction under new actions, and when it remains useful after ordinary feedback is available. Recoverable fast/slow contact dynamics are the first instrumented carrier. The candidate contribution is a reproducible information-and-decision boundary or a specifically justified inference mechanism, not the existence of material memory, the use of long sequences, or a JEPA architecture by itself.

## Novelty evolution record

| Version | Framing | Evidence and revision | Next falsification |
| --- | --- | --- | --- |
| Initial intuition | Different internal force composition requires history | Preserved as the physical motivation; partial observation rather than non-Markov physics | X01 with all deployed spatial measurements matched |
| Long-history interpretation | Slow internal modes require a long state sequence | Rejected as an established claim: short observer nearly matches the long network; histories contain observations/actions, not hidden truth | Window, excitation and noise study with strong observers |
| Current candidate | Identify and retain the information that remains relevant to future interaction and action | Preserves history dependence/controller transfer evidence and shared feedback negative result; no confirmed algorithmic novelty | X03-X06 with restricted true-state reference and normal feedback |

Reference for the short-window reasoning: [Stanford EE363 observability and state estimation](https://ee363.stanford.edu/lectures/011_observ.pdf). The equations above are derived for this project's existing law. No new physical experiment or method reproduction was run for this clarification.

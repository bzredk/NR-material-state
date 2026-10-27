# Material memory for robot manipulation: research decision and study plan

Version: 0.1, 2026-10-23. Status: **research audit and proposed protocol; no new robot simulation results**.

The required sequence is spatial 2D contact, qualified 3D articulated-robot simulation, then physical robot experiments. A prescribed indenter trajectory, a soft-body animation, or a robot rendered around a kinematic tool does not satisfy the second stage.

The broad claim that interaction history can initialize a latent material state for prediction and control is already substantially covered by prior work. The present evidence also does not establish a neural estimator advantage over a correctly specified classical observer, or a useful closed-loop action advantage. Stop defending that claim. Investigate the narrower question in [novelty_decision.md](novelty_decision.md) only with the falsification gates in [protocol.md](protocol.md).

## Contents

| File | Purpose |
| --- | --- |
| [novelty_decision.md](novelty_decision.md) | Collision audit, conditional research direction, Nadia feedback and thesis-roadmap traceability |
| [literature.md](literature.md) | Seventeen primary-source method cards with inspected pages and contribution limits |
| [protocol.md](protocol.md) | Physics qualification, two robot tasks, fair comparisons, statistics, reproducibility, and stopping rules |
| [eval_spec.json](eval_spec.json) | Machine-readable evaluation contract; proposed values, not completed checks |
| [tools/plan_power.py](tools/plan_power.py) | Reproducible approximate sample-size and workload arithmetic |
| [reports/planning_estimates.json](reports/planning_estimates.json) | Planning arithmetic only; no scientific observations |
| [review_log.md](review_log.md) | Adversarial review, remaining uncertainties, and version decisions |

## Evidence locations

- Current project evidence: [1D/RESULTS.md](../../1D/RESULTS.md).
- Earlier spatial 2D design: [plans/2d_contact](../2d_contact/README.md). Its results have not been invented or promoted to robot evidence here.
- Full-text source archive, checksums, search ledger, and Chinese report: `../../../Documents/Codex/2026-10-23-novelty-experiment-audit/`.
- Audio evidence: `../../../Documents/Codex/2026-10-23-project-feedback/`. Chinese recaps and the incomplete English teacher fragment have different evidentiary status.
- Research-roadmap source: [Physical Grounded AI](https://thesis-spine.link/thesis-spine-rendered), retrieved 2026-10-23.

## Next implementation milestone

Build a small physics qualification slice before training another large model: two physically replayed histories, elastic and viscoelastic controls, a true planar mesh with lateral measurements, and a classical state observer. If this produces an observable, numerically stable history effect, qualify a 7-DoF robot coupled to the 3D material model. Only then freeze the robot benchmark and final sample sizes.

The simulator backend, physical material calibration, robot hardware, and final sample sizes remain open implementation choices. The plan gives defaults and acceptance conditions; it does not claim those dependencies already work. Existing experiment folders and results are preserved.

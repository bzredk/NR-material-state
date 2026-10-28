# Hidden object state: research convergence package

Date: 2026-10-25. Status: **evidence audit and executable experiment design**. Existing results are preserved. No new model training, physical experiment, or 2D/3D simulation study was run in this review. Plot reconstruction and document/contract checks are separate from scientific validation.

The central question is how an embodied system infers and retains an object's hidden dynamic state well enough to predict future interactions and know when that understanding is adequate for a decision. Recoverable materials are the current physical carrier. The recommended target is B, predictive state; A, physical coordinates, is the reference; C, belief, is conditional on useful unresolved ambiguity.

## Requested deliverables

| Deliverable | File | Status |
| --- | --- | --- |
| 1. One-page positioning | [research_position.md](research_position.md) | Evidence-based candidate, not established novelty |
| 2. Overall research matrix | [frameworks.md](frameworks.md) | C01-C06 mapped to the six overall axes |
| 3. Mechanism/validation matrix | [frameworks.md](frameworks.md) | Same C01-C06, distinct six mechanism axes |
| 4. Traceable crosswalk | [registry.json](registry.json), [formalization.md](formalization.md) | Q/C/D/X/V/source IDs and state definitions |
| 5. Closest-work comparison | [closest_work.md](closest_work.md), [literature_registry.json](literature_registry.json) | Five priority methods, primary text/code/data checks and access limits |
| 6. Resources and platforms | [resources_platforms.md](resources_platforms.md) | Requestable equipment distinguished from assigned/measured capabilities |
| 7. Minimal complete experiment | [minimal_experiment.md](minimal_experiment.md), [eval_spec.json](eval_spec.json) | Proposed; calibration, timing and decision thresholds remain unfrozen |
| 8. Staged route | [roadmap_and_decisions.md](roadmap_and_decisions.md) | Spatial 2D -> qualified articulated 3D -> physical robot |
| 9. Nadia briefing | [nadia_brief.md](nadia_brief.md), [figures](figures) | Two archived-evidence figures and one proposed decision schematic |
| 10. Implementation priorities | [roadmap_and_decisions.md](roadmap_and_decisions.md) | NOW / prerequisite-gated / DEFER with smallest evidence actions |

Chinese synthesis (local source: `2026-10-25-hidden-state-reframing/research_synthesis_zh.md`) provides the connected explanation and decisions. English technical documents remain in this project folder. Source PDFs, website checks, code snapshots and acquisition records remain in the task artifact folder, outside the Git repository.

## What the audit changes

See [existing_evidence.md](existing_evidence.md) for exact sources and assumptions. The known-family classical estimator remains the strongest archived force predictor; a 0.2 s observer nearly matches a 3 s history network. shared feedback retains its negative action result, but common-observer convergence is not proof of recovered truth: the update worsens initially accurate estimates. The saved action batch has no true-state reference. Including shared-prefix cap breaches reduces archived success from the task-window 100% to approximately 84.90%.

Generic history encoding, belief update, internal variables and recurrence are prior art. A contribution remains conditional on establishing a meaningful information-and-decision boundary or a specific inference deficiency under equal conditions. Lack of an identical prior experiment is not a novelty proof. The one-task plan replaces automatic expansion to multiple platforms or large sweeps.

## Reproduction of this review package

From the repository root:

```powershell
python research/hidden_state_reframing/tools/build_nadia_figures.py
python research/hidden_state_reframing/tools/validate_package.py
```

The figure script reads archived arrays and saved summaries only. It fixes illustrative pair index 0 before inspecting the response magnitude. [figure_data.json](figure_data.json) and [figure provenance](figures/provenance.json) record inputs and hashes. The validation script checks sources, links, IDs, JSON structure and the absence of accidental non-English technical prose; these checks do not certify scientific hypotheses or a working simulator.

## Skills and evidence scope

Applied `physics-grounded-world-model`, `paper-novelty-design-v1`, `world-model-evaluation`, `academic-research-suite`, and the PDF reading skill. Their contributions are explicit physical/observation contracts, Problem-Method-Insight boundaries, falsifiable evaluation and grouped statistical design, primary-source reading, and rendered equation checks. The evaluation skill's structural validator passed for `eval_spec.json`; it is not a scientific acceptance test.

The live research roadmap was rechecked on 2026-10-25 and exactly matches the October 23 archive, including its embedded document. Theory/website verification (local source: `2026-10-25-hidden-state-reframing/theory_checks/verification.json`) and theory acquisition manifest (local source: `2026-10-25-hidden-state-reframing/theory_sources.json`) preserve the scope of those checks. Audio is reused from the earlier transcript; incomplete direct English, Chinese meeting recaps and our design choices remain separately labeled.

Current blocking evidence is concrete: no specimen, fixture or real measurement exists; an arm/sensor configuration may be requested but actual interfaces and timing are unknown; the continuum-to-articulated-robot coupling is not built; decision headroom and recursive sufficiency remain untested. Offline interfaces and the smallest physics/observability diagnostic can proceed without treating those unknowns as resolved.

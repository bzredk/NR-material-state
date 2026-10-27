# Observer configuration checks

Local verification on 2026-10-26 in the existing Linux Dev Container. These are software regression checks, not new experimental results.

| Check | Result | Record |
| --- | --- | --- |
| Published vs refactored defaults | Two recorded histories, four methods, noiseless slow press and noisy fast press; largest absolute prediction difference 0.0; 43.46 s | [Numerical regression](numerical_regression.json) |
| Tests | 8 passed, 4.38 s; physical contracts, explicit budgets/windows, cache isolation, CLI and widget configuration | [Pytest](pytest.xml) |
| Fresh Notebook kernel | 9 code cells passed, 5.81 s | [Execution record](notebook.json), [executed copy](executed.ipynb) |
| Widget callbacks | Replay cursor, pause/reset, four actions, two checkpoints, noise and excitation passed; 6.73 s | [Callbacks](callbacks.json) |
| Main figure | Recorded pair, equal future commands, all five endpoint channels, SVG/PDF/300 dpi PNG exported and inspected | [Source data and provenance](../../../docs/figures/hidden_state_pair.json) |

The numerical regression compares displacement, internal fields, tool position/velocity, force and lateral markers against the archived estimator implementation. It also compares force and marker RMSE. The new test settings deliberately use a smaller optimizer budget to verify that the requested settings reach computation and are recorded.

The Notebook check uses a fresh kernel. Callback tests instantiate ipympl and exercise Python callbacks; this round did not repeat native frontend clicks. The previous [native Docker check](../../container_validation/20261026_docker_layout/native_controls.json) remains available.

The homepage figure was inspected at full resolution and at 1008 px width. It uses the original selected pair and all recorded history/future samples. Force and lateral-response axes include zero; geometry is shown at 1:1 deformation scale. SVG and PDF retain editable text. The source preflight has no failures. Its three journal-export warnings concern the requested PNG format, 300 dpi and the wide README/presentation layout; this is not a journal submission package.

Tracked 1D records and the published 2D pilot are unchanged. The physical solver and protocols are unchanged; a full physics/refinement rerun was not needed for this refactor.

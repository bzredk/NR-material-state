# Experiment tools

Run from `2D/` inside the Docker Dev Container.

| Command | Purpose |
| --- | --- |
| `python tools/validate_container.py` | Dependencies, contract tests and a fresh-kernel notebook |
| `python tools/validate_container.py --full` | Add physics refinement, callback checks and figure/animation export |
| `python tools/execute_spatial_notebook.py` | Execute the notebook; save a timestamped record under `runs/notebook_validation/` |
| `python tools/verify_spatial_interactions.py` | Exercise playback, actions and noise/excitation callbacks |
| `python -m nr2d.cli --help` | Generate experiments, evaluate and export figures |
| `python tools/draw_experiment_flow.py` | Rebuild the design diagram as SVG, PNG and PDF |
| `python tools/plot_hidden_state_pair.py` | Rebuild the homepage figure from the recorded pair; export SVG/PDF/PNG, CSV and provenance |
| `python tools/verify_observer_refactor.py` | Compare current default predictions with the published implementation |

`build_spatial_notebook.py` maintains the notebook cells. Numerical code lives in `src/nr2d/`.

`setup_container.py` checks the mounted source and container interpreter. `lock_container_requirements.py` generates the pinned wheel lock. `open_devcontainer.ps1` opens an independent VS Code window on Windows. The persistence helpers test disposable-container replacement.

`archive_spatial_checks.py` and `summarize_spatial_run.py` write into the selected run. Use a new run for new evidence.

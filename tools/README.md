# Project tools

Run these commands from the repository root, inside the Dev Container unless noted.

| Command | Purpose |
| --- | --- |
| `python tools/validate_container.py` | Dependency check, four contract tests and a fresh-kernel notebook |
| `python tools/validate_container.py --full` | Add physical refinement, callback checks and figure/animation export |
| `python tools/execute_spatial_notebook.py` | Execute the notebook and save a timestamped result in `runs/notebook_validation/` |
| `python tools/verify_spatial_interactions.py` | Exercise playback, actions and noise/excitation callbacks in a fresh kernel |
| `python -m nr2d.cli --help` | Generate experiments, run batches and export figures |

`build_spatial_notebook.py` rebuilds the notebook from its maintained cell definitions. Numerical code lives in `src/nr2d/`.

Infrastructure helpers:

- `setup_container.py`: editable package installation after container creation.
- `lock_container_requirements.py`: generate the pinned wheel lock from a Linux pip report.
- `open_devcontainer.ps1`: launch an independent VS Code window on Windows.
- `verify_container_persistence.ps1` / `container_persistence.py`: optional disposable-container persistence check.
- `notebook_server.py`: legacy Windows notebook backend.
- `restore_workcopy.py`: recover an archived 1D local workcopy; see the [snapshot guide](../runs/workcopy_archive/20261026_cleanup/README.md).

`archive_spatial_checks.py` and `summarize_spatial_run.py` write evidence into the selected run. Use them for a new run rather than overwriting a published record.

# Linux Dev Container

The current 2D demo runs on CPU. The image pins Python 3.11.9 and 98 Python packages with wheel hashes. It includes Jupyter, ipykernel, ipywidgets and ipympl. CUDA and the archived GPU training stack are outside this image's scope.

## Open and run

1. Start Docker Desktop with the Linux engine.
2. Open `D:\capp\NR\NR-material-state` in VS Code. Install **Dev Containers** if needed.
3. Run **Dev Containers: Reopen in Container** from the command palette.
4. Open `2D/spatial_2d_hidden_state.ipynb`.
5. Choose **Select Kernel > Python Environments > venv (Python 3.11.9)**, path `/opt/venv/bin/python`. Some kernel menus show the registered name **NR Spatial 2D (Linux)**.
6. Choose **Restart**, then **Run All**. A newly selected, unused kernel is already clean.

The container installs the Python and Jupyter extensions and attaches the source with an editable install. No browser or external notebook server is needed. Hide the sidebars with **Ctrl+B** and **Ctrl+Alt+B** for a full-width presentation.

On this Windows machine, `tools/open_devcontainer.ps1` opens a separate VS Code instance through WMI with `CREATE_BREAKAWAY_FROM_JOB`. Its app state is kept in `.runtime/vscode-container`. This avoids reusing the earlier Codex-launched window. Folder trust is a user choice on first launch. The container's `shutdownAction` is `none`, so closing VS Code leaves the container running.

## Build and verify from PowerShell

Run from the project directory:

```powershell
docker build --progress=plain -t nr-spatial-2d:py311 .
docker run --rm `
  --mount "type=bind,source=$($PWD.Path),target=/workspaces/NR-material-state" `
  nr-spatial-2d:py311 /bin/bash -c `
  '/opt/venv/bin/python tools/setup_container.py && /opt/venv/bin/python tools/validate_container.py'
```

The second command runs the daily check: dependencies, contract tests and one fresh-kernel notebook. Results go to `runs/container_validation/<UTC timestamp>/`.

Inside the Dev Container, the equivalent is:

```sh
python tools/validate_container.py          # Daily check
python tools/validate_container.py --full   # Before a release or after physics changes
python -m nr2d.cli demo --recompute
python -m nr2d.cli batch
```

`demo --recompute` creates a new pilot. A normal notebook Run All computes a fresh main episode and reuses labeled prediction/verification caches. `--full` adds fresh physics/refinement checks, the archived trajectory comparison, widget callback tests and PNG/SVG/PDF/GIF export.

## Storage and reproducibility

| Item | Location |
| --- | --- |
| Code, notebook, data, outputs | Host project, bound to `/workspaces/NR-material-state` |
| Linux Python environment | `/opt/venv`, built from `requirements-container.txt` |
| Original Windows environment | Host `.venv`, preserved; never copied into the image or selected in Linux |
| VS Code server/extensions | Container; recreated on rebuild |
| New verification evidence | `runs/container_validation/` on the host |

The project is a bind mount, so results survive container replacement. The Windows `.venv` stays on the host; Linux uses `/opt/venv`.
The base image and Python wheels are pinned. OS package versions are recorded with full validation; Debian security updates may change a future uncached build.

To repeat the removal/rebuild persistence test after a full validation run:

```powershell
.\tools\verify_container_persistence.ps1 -RunName <validation-directory-name>
```

This optional infrastructure check removes a disposable container, rebuilds the image and checks the saved results from a second container.

## Dependency changes

Edit `requirements-container.in`, then resolve **inside Linux/amd64 CPython 3.11.9** with `pip install --dry-run --ignore-installed --only-binary=:all: --report <report.json> -r requirements-container.in`. Run `python tools/lock_container_requirements.py <report.json> requirements-container.txt`, rebuild, and repeat validation. Resolve the lock in Linux so its wheel hashes match the container.

The current results and timings are in [CONTAINER_VALIDATION.md](CONTAINER_VALIDATION.md).

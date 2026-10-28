# Run in Docker

The 2D experiment runs on CPU in a Linux container. Python 3.11.9, Jupyter, ipykernel, ipywidgets and ipympl are installed in the image. VS Code lists the container kernel as **Python 3.11.9**; its registered Jupyter name is **NR 2D (Docker)**.

## VS Code

1. Start Docker Desktop with the Linux engine.
2. Open the repository root in VS Code and install **Dev Containers**.
3. Choose **Dev Containers: Reopen in Container**. To replace the earlier image, use **Rebuild and Reopen in Container**.
4. Open `2D/notebooks/spatial_2d_hidden_state.ipynb`.
5. Select the container's **Python 3.11.9**, then **Restart** and **Run All**.

The status bar should show **Dev Container: NR 2D Docker**. The image's interpreter is `/usr/local/bin/python`; it is selected by the container configuration. The terminal starts in `2D/`.

Python and Jupyter extensions are configured in [devcontainer.json](../../.devcontainer/devcontainer.json). On Windows, `2D/tools/open_devcontainer.ps1` launches an independent VS Code window through WMI.

## Build and run from PowerShell

From the repository root:

```powershell
docker build --progress=plain -t nr-spatial-2d:py311 2D/environment
docker run --rm `
  --mount "type=bind,source=$($PWD.Path),target=/workspaces/NR-object-state" `
  nr-spatial-2d:py311 python tools/validate_container.py
```

Inside the Dev Container, from `2D/`:

```sh
python tools/validate_container.py
python tools/validate_container.py --full
python -m nr2d.cli demo --config configs/spatial_contact.json --recompute
python -m nr2d.cli batch
python -m nr2d.cli export
```

The daily check runs dependency validation, contract tests and a fresh notebook kernel. `--full` adds physics/refinement checks, widget callbacks, archived-trajectory comparison and PNG/SVG/PDF/GIF export.

## Files and persistence

| Location | Contents |
| --- | --- |
| `2D/environment/` | Dockerfile and pinned dependencies |
| `2D/configs/` | Physical run configuration |
| `2D/runs/` | Host-mounted data and outputs; retained after container replacement |
| Image filesystem | Python packages and kernel registration |

The image pins the Python base digest and 98 package versions with wheel hashes. It loads `2D/src/` from the bind mount. Python and Jupyter run inside the container; code, settings and results stay on the host. CUDA is not part of this CPU image.

To update dependencies, edit `environment/requirements-container.in`, resolve wheels inside Linux/amd64 Python 3.11.9, and use `tools/lock_container_requirements.py` to write the lock. Rebuild and run the full check.

[Configuration details](CONFIGURATION.md) · [Measured validation](CONTAINER_VALIDATION.md)

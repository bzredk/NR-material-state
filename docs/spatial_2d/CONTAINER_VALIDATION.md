# Container validation — 2026-10-26

**Passed on this machine.** Linux/amd64, Python 3.11.9, Docker Engine 29.1.3, VS Code 1.105.1. The engine exposed 24 CPUs and 23.34 GiB RAM; BLAS/OpenMP threads were limited to one. This record covers the CPU 2D demo.

| Check | Actual result |
| --- | --- |
| Image build | Passed; base digest and 98 wheel versions/hashes pinned |
| Dev Container post-create | Passed; mounted source installed in `/opt/venv` |
| Dependency consistency | `pip check` passed |
| Contract tests | 4 passed, 1.46 s |
| Fresh physics checks | 17/17, 17.90 s |
| Fresh-kernel notebook via nbclient | 9 code cells, no errors, 8.71 s including kernel startup |
| Native VS Code first Run All | 9 code cells, no errors; notebook body 5.70 s |
| Native Restart, then Run All | 9 code cells numbered 1–9, no errors; body 6.40 s; fresh main solve 1.49 s |
| Widget callback suite | Passed, 9.97 s in a fresh kernel |
| Native frontend | Play/pause/reset, slider and shared cursors, future-action dropdown, progress, curve refresh and noise sweep passed |
| Fresh Fast press forecasts from GUI | Four estimates recomputed, 6.90 s; prior results retained |
| Fresh Linux figure/animation export | PNG, SVG, PDF and 93-frame GIF; export 73.43 s |
| Full automated validation | 138.40 s including physics, notebook, callbacks and export |
| Persistence | First disposable container removed; image rebuilt; second container verified 23 unchanged artifact hashes |

The notebook's timing includes a **fresh main physical trajectory** and labeled replay of existing pilot checks/predictions. It is not the time for a new full pilot. The separate automated validation recomputed all 17 checks.

The fresh Linux main episode exactly matched the archived Windows arrays for force, displacement, internal strain, tool position/velocity and lateral markers. This is a check for this configuration, not a guarantee of bitwise equivalence across all machines or future experiments. Numerical scope and the retained negative results did not change.

## Evidence

After moving the main notebook to `2D/`, the [repository publication check](../../runs/container_validation/20261026_repo_publish/validation.json) passed in 20.63 s: dependencies, four contract tests and nine code cells in a fresh kernel (6.74 s). The separate [widget callback check](../../runs/container_validation/20261026_repo_publish/callbacks.json) passed in 7.16 s. The physical implementation is unchanged; the native frontend observations below are the earlier direct VS Code checks.

All paths below are under [`runs/container_validation/20261026_linux_cpu`](../../runs/container_validation/20261026_linux_cpu):

- [Automated result](../../runs/container_validation/20261026_linux_cpu/validation.json), [physics](../../runs/container_validation/20261026_linux_cpu/physics_checks.json), [tests](../../runs/container_validation/20261026_linux_cpu/pytest.log).
- [Executed notebook](../../runs/container_validation/20261026_linux_cpu/executed.ipynb), [native frontend after Restart](../../runs/container_validation/20261026_linux_cpu/frontend_after_restart.ipynb), [frontend observations](../../runs/container_validation/20261026_linux_cpu/frontend_checks.json).
- [PNG](../../runs/container_validation/20261026_linux_cpu/spatial_process.png), [SVG](../../runs/container_validation/20261026_linux_cpu/spatial_process.svg), [PDF](../../runs/container_validation/20261026_linux_cpu/spatial_process.pdf), [GIF](../../runs/container_validation/20261026_linux_cpu/spatial_process.gif), raw `main.npz` and `figure_provenance.json`.
- [Image and mount record](../../runs/container_validation/20261026_linux_cpu/container_manifest.json), [persistence](../../runs/container_validation/20261026_linux_cpu/persistence.json), dependency/build logs and source hashes.

## Resolved setup issues and limits

Docker initially failed on two stale runtime sockets. Its old runtime directory was retained and replaced; no images, volumes or experiment data were deleted. The first post-create check tried to import an editable package in the interpreter that had just installed its `.pth` file. Checking in a new interpreter fixed that issue; both the failure and successful retry are retained.

The Jupyter extension logged a failed CDN fetch. Installed widget assets still rendered and supported all observed interactions; no third-party download permission was enabled. No browser or separate Jupyter server was used for the Linux frontend.

The independent VS Code process was launched through WMI with `CREATE_BREAKAWAY_FROM_JOB`, verified with a WMI parent and exclusion from the current Codex command job. The container remains running when VS Code closes. Closing Codex itself was not tested.

The Windows `.venv` remains in place. It is excluded from the image and was not used as the Linux interpreter. CUDA, GPU training, full 3D manipulation and real-material validation were not tested in this migration.

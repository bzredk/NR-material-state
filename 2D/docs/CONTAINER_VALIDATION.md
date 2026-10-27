# Docker validation

The current image uses Python 3.11.9 at `/usr/local/bin/python`, with kernel **NR 2D (Docker)**. It was rebuilt after the repository reorganization.

These measurements precede the observer-configuration refactor. Its targeted numerical, configuration and Notebook checks are indexed [separately](../runs/implementation_checks/observer_config/README.md).

| Check | Measured result |
| --- | --- |
| Dependency consistency | Passed |
| Contract tests | 4 passed, 1.22 s |
| Physical checks | 17/17 passed, 16.62 s |
| Fresh-kernel notebook | 9 code cells, 7.40 s |
| Native VS Code Run All | 9 code cells, 5.72 s notebook body |
| Widget callbacks | Passed, 7.40 s |
| Native controls | Timeline, synchronized curves, Play, Pause and Reset verified |
| Reference trajectory | Force, displacement, internal fields, tool motion and markers match the saved pilot |
| Full validation | 104.99 s, including PNG/SVG/PDF/GIF export |

[Run record](../runs/container_validation/20261026_docker_layout/validation.json) · [Executed notebook](../runs/container_validation/20261026_docker_layout/executed.ipynb) · [Physics](../runs/container_validation/20261026_docker_layout/physics_checks.json) · [Callbacks](../runs/container_validation/20261026_docker_layout/callbacks.json) · [Native execution](../runs/container_validation/20261026_docker_layout/native_execution.json) · [Native controls](../runs/container_validation/20261026_docker_layout/native_controls.json)

The Dev Container was rebuilt and connected as **NR 2D Docker**. Its post-create check imports the mounted `2D/src/` implementation successfully. The five numerical modules are byte-for-byte unchanged by the layout migration; the 741 archived research artifacts also pass their original hashes through the recorded path mapping.

The [spatial animation](../runs/2d_contact/pilot_c9dd23016896/figures/01_spatial_process.gif) is stored once with the scientific pilot. The current setup instructions are in [CONTAINER.md](CONTAINER.md).

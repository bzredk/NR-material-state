# Setup

This repository runs as Python scripts on a workstation or a compute server. There is no service to start, web port to expose, account to configure or API key to supply. The synthetic datasets and trained weights are included in the checkout.

[中文说明](SETUP.zh-CN.md) · [Experiment commands](REPRODUCING.md) · [Results](RESULTS.md)

## Choose what you want to run

| Task | CPU installation | CUDA installation |
| --- | --- | --- |
| Read the slides, figures and JSON/CSV results | Python is unnecessary | Python is unnecessary |
| Check file hashes and saved result summaries | Yes; these two checks use the Python standard library | Yes |
| Replay the 24 primary checkpoints on small inputs | Yes | Yes |
| Run the three groups of correctness tests | Yes | Yes |
| Train history dependence/controller transfer or rerun their full evaluation entry points | No; the recorded entry points use CUDA | Yes |
| Recompute shared feedback statistics and figures from saved trajectories | Yes | Yes |
| Run shared feedback again from frozen encoders | The `prepare` stage needs CUDA; later rollouts use CPU/Numba | Yes |
| Prepare a material collection session and inspect exported measurements | Yes | Yes |

If you only want to check the results, choose CPU. Installing a CUDA build will not make the CPU mechanics solver run on the GPU.

## Environment and disk space

Use 64-bit Python 3.11. The original experiments used Python 3.11.9, PyTorch 2.9.1 with CUDA 12.8, and an NVIDIA RTX 5070 Ti with about 16 GiB of GPU memory. That is the recorded machine, not a measured minimum hardware requirement.

The checked-out archive is about 650 MB. Allow roughly 10 GB free for Git's local object store, packages, download caches and a few working copies; fresh training will need additional space as runs accumulate. This is a planning allowance, not a disk benchmark. For a GPU run, inspect the experiment's generated `profile.json` on your machine before estimating time or memory needs.

The direct dependencies are pinned in [`1D/requirements.txt`](requirements.txt). PyTorch is installed separately so you can choose CPU or CUDA. Transitive dependencies are not fully locked; save `pip freeze` with a new run if you need to record its exact environment.

The steps below have been exercised on Windows with a fresh CPU environment. The archived experiments used Windows/CUDA. Linux commands are provided for the same entry points, but this documentation update does not include a Linux training run. macOS, Apple MPS and ROCm training are not covered by these instructions.

## Windows PowerShell

Install [Git for Windows](https://git-scm.com/downloads/win) and a 64-bit [Python 3.11 interpreter](https://www.python.org/downloads/release/python-3119/) first. Open a new PowerShell window in the parent folder where you want the project.

### 1. Clone and create the environment

```powershell
git --version
py -3.11 --version
git clone https://github.com/bzredk/NR-material-state.git
Set-Location NR-material-state
py -3.11 -m venv .venv
$env:Path = (Join-Path (Get-Location) '.venv\Scripts') + ';' + $env:Path
python -c "import sys; print(sys.executable); print(sys.version)"
python -m pip install --upgrade pip
python -m pip install -r '1D/requirements.txt'
```

The printed executable should end in `NR-material-state\.venv\Scripts\python.exe`. If you already cloned the project, enter that folder and start at the environment step. If `py` is unavailable but `python --version` reports 3.11, use `python -m venv .venv` instead.

Adding `.venv\Scripts` to this terminal's PATH lets the remaining commands use `python` from any experiment folder. It does not change the system PATH or PowerShell's execution policy. [Python's venv documentation](https://docs.python.org/3.11/library/venv.html) also supports using the environment's executable directly without activation.

### 2. Install one PyTorch build

For CPU:

```powershell
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu
```

For an NVIDIA GPU:

```powershell
nvidia-smi
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
```

The GPU route requires a working NVIDIA driver and a GPU supported by that wheel. If `nvidia-smi` fails, resolve the driver/device access first. These wheel selections follow the [official PyTorch 2.9.1 installation table](https://pytorch.org/get-started/previous-versions/#v291); this project does not need `torchvision` or `torchaudio`.

Install only one route in a new environment. If you already installed CPU PyTorch and now need CUDA, replace it explicitly:

```powershell
python -m pip uninstall -y torch
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
```

### 3. Check the installation

```powershell
python -m pip check
python '1D/tools/check_environment.py'
```

For a GPU installation, also run:

```powershell
python '1D/tools/check_environment.py' --require-cuda
```

Expect `No broken requirements found` from pip and `"status": "passed"` from the checker. CPU mode reports `"available": false` under `cuda`; that is expected. CUDA mode should report the device name and pass an actual tensor calculation. The checker also imports the pinned packages and runs a small Numba calculation. Version differences appear as warnings; use the pinned versions for the documented environment.

### Returning in a new terminal

Enter your clone, then restore the environment for that terminal:

```powershell
$env:Path = (Join-Path (Get-Location) '.venv\Scripts') + ';' + $env:Path
python -c "import sys; print(sys.executable)"
```

Run these two lines from the repository root, before entering an experiment folder. There is no need to reinstall packages each time.

## Linux, including an SSH compute session

Start with Git, a 64-bit `python3.11`, and its `venv` support installed on the host. Distribution package names differ; if `python3.11 -m venv` reports that `ensurepip` is missing, install the venv package matching that interpreter through your distribution or administrator.

Run in Bash:

```bash
git clone https://github.com/bzredk/NR-material-state.git
cd NR-material-state
python3.11 -m venv .venv
source .venv/bin/activate
python -c "import sys; print(sys.executable); print(sys.version)"
python -m pip install --upgrade pip
python -m pip install -r '1D/requirements.txt'
```

Choose one PyTorch command:

```bash
# CPU
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu
```

```bash
# NVIDIA GPU
nvidia-smi
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
```

Then check it:

```bash
export MPLBACKEND=Agg
python -m pip check
python '1D/tools/check_environment.py'
# Add this check before a GPU experiment:
python '1D/tools/check_environment.py' --require-cuda
```

Omit the last command for a CPU installation. `MPLBACKEND=Agg` lets plotting run without a display. In a fresh SSH session, enter the clone and run `source .venv/bin/activate` again. On a cluster, run the CUDA check inside your allocated GPU job; a login node may not expose a GPU. Use the site's scheduler or an existing terminal multiplexer for long jobs, and record stdout/stderr with the run. No repository-specific daemon or scheduler configuration is required.

## Check the archive before changing anything

From the repository root, in the environment you just installed:

```sh
python "1D/tools/verify_bundle.py"
python "1D/tools/check_results.py"
python "1D/tools/replay_checkpoints.py"
```

| Command | What a successful run shows |
| --- | --- |
| `verify_bundle.py` | `status: passed`, a file count, 12 slides and three diagram formats. It checks archived research hashes and experiment source text. Use `--strict-snapshot` to also compare documentation and helpers with the historical release. |
| `check_results.py` | 24 converged primary training records, six matching frozen checkpoints, and the archived history dependence/controller transfer/shared feedback metrics. |
| `replay_checkpoints.py` | Two result blocks, each with `checkpoints_replayed: 12` and finite predictions. history dependence reports differences from saved predictions; CUDA mode also enforces the original tolerance. |

The replay loads all primary checkpoints but evaluates only small input slices. It is a useful installation check, not a replacement for the full experiment evaluation. On first use, Numba may spend time compiling before it prints output.

The archive was produced on CUDA. CPU recurrent kernels can give different accumulated trajectories: the fresh CPU check observed a maximum history dependence force difference of about 0.00252 N on the sampled pair. CPU mode labels its comparison `cpu_diagnostic_only` and reports whether each model meets the unchanged CUDA tolerance. It does not claim numerical parity. Use `--device cuda` to check with the original tolerance, or `--device cpu --strict-archive` if you deliberately want the same strict assertion on CPU.

Run the tests as three separate commands:

```sh
python -m pytest -q "1D/experiments/pilot/test_pilot.py"
python -m pytest -q "1D/experiments/history_dependence/test_round2.py" "1D/experiments/history_dependence/test_intake.py"
python -m pytest -q "1D/experiments/controller_transfer/v2/test_core.py"
```

The expected counts are 5, 9 and 8 passed. Do not collect the whole archive with one `pytest` command: independent experiments reuse module names such as `models.py` and `physics.py`.

## Run an experiment and find its outputs

Follow the [step-by-step reproduction guide](REPRODUCING.md). It creates copies under `reproductions/` before running scripts that write results. That folder, `.venv/` and generated caches are ignored by Git.

| Experiment | Main output in its working copy |
| --- | --- |
| history dependence | `runs/replication/summary.json`, `predictions.npz`, `checkpoints/`, `logs/`, `figures/` |
| controller transfer | `v2/runs/transfer_v2/`, plus `v2/figures/` |
| shared feedback | `raw/`, `results/summary.json`, `results/episode_metrics.csv`, `figures/` |
| material collection | Your chosen `collection/`, `data/` and `runs/` paths inside the lab working copy |

Save the Git revision and package list with new work. For example, from the repository root:

```sh
python -c "from pathlib import Path; Path('reproductions').mkdir(exist_ok=True)"
git rev-parse HEAD > reproductions/source-commit.txt
python -m pip freeze > reproductions/environment.txt
```

## Optional exports

The material collection execution card is already included as PDF. To rebuild it, install `reportlab` and `pypdfium2`, then run `build_card.py` in the lab working copy. They are not needed for scheduling or data intake.

The workflow drawing also has ready-made PNG, SVG and PDF exports. Its Python source requests Arial. A machine without that font may substitute another font and change the layout; use the saved export when identical presentation appearance matters.

## Common problems

| Symptom | What to check |
| --- | --- |
| `ModuleNotFoundError` after installation | Print `sys.executable`; make sure it points into this clone's `.venv`. Always use `python -m pip` with that same interpreter. |
| `CUDA required for this recorded experiment` | The full history dependence entry point also requires CUDA for `evaluate`. Use the small replay tool on CPU, or install the CUDA environment for full evaluation. |
| `torch.cuda.is_available()` is false | Check `nvidia-smi`, the PyTorch build shown by `check_environment.py`, and whether your job can see a GPU. A CPU wheel remains a CPU wheel even on a GPU machine. |
| No compatible wheel / dependency conflict | Check Python is 3.11 and 64-bit. Use a clean venv and the pinned requirements. Avoid upgrading NumPy alone in an existing Numba environment. |
| `Destination exists` from `workcopy.py` | Choose a new copy name, such as `reproductions/history-dependence_second`. The helper will not overwrite an earlier run. |
| controller transfer training exits quickly | It skips models whose saved metadata already says `converged`. Follow the fresh-run instructions to archive the copied `runs/transfer_v2` directory first. |
| Evaluation rejects a run | Check its `logs/*_meta.json`. Reaching the update cap is not the same as satisfying the validation plateau rule. Resume as documented; keep any altered training budget with the new run. |
| Hash mismatch | Check whether an archived file was edited or overwritten. Run experiments in a work copy. A new clone is the simplest way to recover an untouched reference; do not replace reference hashes to hide a changed result. |
| `Project-local outputs required` | history dependence output paths must stay inside its working-copy directory. material collection similarly keeps session output inside its own copy. |
| A command cannot find `1D/` | Start from the repository root and use the current experiment paths in this guide. |
| Plotting fails on a server | Set `MPLBACKEND=Agg`; check font availability if only the figure appearance differs. |

When reporting a problem, include the command, starting directory, full error text, Git revision and the output of `check_environment.py`. Those details are more useful than a screenshot of the final error line.

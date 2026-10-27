"""Check the container and notebook; use --full for physics, callbacks and exports."""
import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import traceback

import numpy as np
from nr2d.checks import run_checks
from nr2d.experiments import ROOT, environment, source_hashes, write_json
from nr2d.physics import Trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--full", action="store_true",
                        help="Add physics refinement, callbacks, archive comparison and figure/GIF export.")
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("Run this check in the Linux container.")
    out = args.output or ROOT / "runs/container_validation" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    record = {"status": "running", "mode": "full" if args.full else "quick", "platform": platform.platform(), "python": sys.executable,
              "environment": environment(), "device": "CPU", "steps": []}
    write_json(out / "validation.json", record)

    def command(label, argv):
        t = time.perf_counter()
        with (out / f"{label}.log").open("w", encoding="utf-8") as stream:
            proc = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        record["steps"].append({"step": label, "command": argv, "exit_code": proc.returncode,
                                "wall_seconds": time.perf_counter() - t})
        write_json(out / "validation.json", record)
        print(f"{label}: exit {proc.returncode}", flush=True)
        proc.check_returncode()

    try:
        command("pip_check", [sys.executable, "-m", "pip", "check"])
        command("pytest", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={out / 'pytest.xml'}"])
        if args.full:
            for name in ("Dockerfile", "requirements-container.in", "requirements-container.txt"):
                shutil.copy2(ROOT / "environment" / name, out / name)
            shutil.copy2(ROOT.parent / ".devcontainer/devcontainer.json", out / "devcontainer.json")
            shutil.copy2("/usr/local/share/nr2d/system-packages.tsv", out / "system-packages.tsv")
            command("pip_freeze", [sys.executable, "-m", "pip", "freeze", "--all"])
            checks, trace = run_checks()
            write_json(out / "physics_checks.json", checks)
            trace.metadata.update(source="Fresh Linux container solve", role="environment validation")
            trace.save(out / "main.npz")
            assert checks["passed"], "Fresh physics checks failed; see physics_checks.json"
            print(f"Physics: {sum(r['passed'] for r in checks['rows'])}/{len(checks['rows'])} ({checks['wall_seconds']:.2f}s)", flush=True)
            archived = Trace.load(ROOT / "runs/2d_contact/pilot_c9dd23016896/main.npz")
            differences = {}
            for channel in ("force", "u", "z", "d", "v", "markers"):
                a, b = getattr(trace, channel), getattr(archived, channel)
                scale = max(float(np.max(np.abs(b))), 1e-12)
                differences[channel] = {"max_abs": float(np.max(np.abs(a-b))), "relative_to_peak": float(np.max(np.abs(a-b))/scale)}
            write_json(out / "linux_windows_comparison.json", differences)
            assert max(v["relative_to_peak"] for v in differences.values()) < 1e-8
        command("notebook", [sys.executable, "tools/execute_spatial_notebook.py", "--output", str(out / "executed.ipynb"),
                             "--record", str(out / "notebook.json")])
        if args.full:
            command("callbacks", [sys.executable, "tools/verify_spatial_interactions.py", "--record", str(out / "callbacks.json")])

            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.animation import FuncAnimation, PillowWriter
            from nr2d.plotting import ReplayFigure
            t = time.perf_counter()
            view = ReplayFigure(trace)
            view.update(int(np.argmax(trace.force)))
            for suffix in ("png", "svg", "pdf"):
                view.fig.savefig(out / f"spatial_process.{suffix}", dpi=300, bbox_inches="tight")
            frames = np.unique(np.r_[np.arange(0, len(trace.time), 3), len(trace.time)-1])
            movie = FuncAnimation(view.fig, view.update, frames=frames, interval=60, blit=False)
            movie.save(out / "spatial_process.gif", writer=PillowWriter(fps=17), dpi=80)
            plt.close(view.fig)
            write_json(out / "figure_provenance.json", {"data": "main.npz", "config": trace.config,
                        "source_sha256": source_hashes(), "frames": len(frames), "fps": 17,
                        "wall_seconds": time.perf_counter()-t, "deformation_scale": 1})
        record["status"] = "passed"
    except Exception:
        record["status"] = "failed"
        record["error"] = traceback.format_exc()
        raise
    finally:
        record["wall_seconds"] = time.perf_counter()-start
        write_json(out / "validation.json", record)
        if args.full:
            hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name != "sha256.json"}
            write_json(out / "sha256.json", hashes)
        print(out, flush=True)


if __name__ == "__main__":
    main()

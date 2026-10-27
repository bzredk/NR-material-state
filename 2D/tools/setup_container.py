"""Check the Docker interpreter and the source supplied by the project bind mount."""
import json
from pathlib import Path
import subprocess
import sys

if sys.platform != "linux" or not Path("/.dockerenv").exists():
    raise RuntimeError("Run this setup inside the project's Docker container.")
root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "-m", "pip", "check"], check=True)
from nr2d.physics import Config, SpatialModel
import nr2d
assert Path(nr2d.__file__).resolve().is_relative_to(root / "src")
assert SpatialModel(Config()).nodes.shape[1] == 2
record = root / ".runtime/container/setup.json"
record.parent.mkdir(parents=True, exist_ok=True)
record.write_text(json.dumps({"status": "passed", "python": sys.executable, "platform": sys.platform,
                              "project": str(root), "kernel": "NR 2D (Docker)",
                              "container": True, "source": nr2d.__file__}, indent=2) + "\n")
print("Ready: NR 2D (Docker). Source and results are bind-mounted.")

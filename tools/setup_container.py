"""Attach the mounted source to the image's Linux interpreter without resolving dependencies."""
import json
from pathlib import Path
import subprocess
import sys

if sys.platform != "linux" or sys.prefix != "/opt/venv":
    raise RuntimeError("Run this setup with /opt/venv/bin/python inside the Linux container.")
root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", str(root)], check=True)
subprocess.run([sys.executable, "-m", "pip", "check"], check=True)
# A new interpreter reads the newly installed editable .pth file.
subprocess.run([sys.executable, "-c", "from nr2d.physics import Config, SpatialModel; assert SpatialModel(Config()).nodes.shape[1] == 2"], check=True)
record = root / ".runtime/container/setup.json"
record.parent.mkdir(parents=True, exist_ok=True)
record.write_text(json.dumps({"status": "passed", "python": sys.executable, "platform": sys.platform,
                              "project": str(root), "kernel": "NR Spatial 2D (Linux)"}, indent=2) + "\n")
print("Ready: NR Spatial 2D (Linux). Source and results are bind-mounted.")

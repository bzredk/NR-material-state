"""Write/read a result marker across two disposable Linux containers."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("phase", choices=["write", "verify"])
parser.add_argument("run", type=Path)
args = parser.parse_args()
assert sys.platform == "linux"
run = args.run.resolve()
assert run.is_relative_to(Path("/workspaces/NR-object-state/2D/runs/container_validation"))
assert json.loads((run / "validation.json").read_text())["status"] == "passed"
marker = run / "persistence_marker.json"
if args.phase == "write":
    hashes = json.loads((run / "sha256.json").read_text())
    marker.write_text(json.dumps({"created_utc": datetime.now(timezone.utc).isoformat(), "artifacts": hashes}, indent=2))
else:
    hashes = json.loads(marker.read_text())["artifacts"]
    for name, expected in hashes.items():
        assert hashlib.sha256((run / name).read_bytes()).hexdigest() == expected, name
    print(f"Verified {len(hashes)} unchanged artifacts from the previous container.")

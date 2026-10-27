"""Execute in a fresh project kernel, save outputs, and record actual wall time."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import asyncio
import sys
import time
import nbformat
from nbclient import NotebookClient

from nr2d.experiments import ROOT, write_json

path = ROOT/"notebooks/spatial_2d_hidden_state.ipynb"
result_dir = ROOT/"runs/notebook_validation"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=result_dir/"executed.ipynb")
parser.add_argument("--record", type=Path, default=result_dir/"execution.json")
args = parser.parse_args()
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
nb = nbformat.read(path, as_version=4)
started = time.perf_counter()
client = NotebookClient(nb, timeout=600, kernel_name="nr-spatial-state", resources={"metadata": {"path": str(ROOT)}},
                        record_timing=True, store_widget_state=True)
client.execute()
nbformat.validate(nb)
args.output.parent.mkdir(parents=True, exist_ok=True)
nbformat.write(nb, args.output)
result = {"status": "passed", "fresh_kernel": True, "wall_seconds": time.perf_counter()-started,
          "code_cells": sum(c.cell_type == "code" for c in nb.cells), "kernel": "nr-spatial-state",
          "platform": sys.platform, "python": sys.executable, "output": str(args.output)}
write_json(args.record, result)
print(result)

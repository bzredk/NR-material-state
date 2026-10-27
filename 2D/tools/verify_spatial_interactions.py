"""Test actual widget callbacks in a fresh notebook kernel without frontend clicks."""
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone
import sys
import time
import nbformat as nbf
from nbclient import NotebookClient
from nr2d.experiments import ROOT, write_json

parser = argparse.ArgumentParser(description=__doc__)
result_dir = ROOT/"runs/notebook_validation"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
parser.add_argument("--record", type=Path, default=result_dir/"interaction_checks.json")
args = parser.parse_args()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
nb = nbf.read(ROOT/"notebooks/spatial_2d_hidden_state.ipynb", as_version=4)
nb.cells.append(nbf.v4.new_code_cell("""
import numpy as np
before = main.u.copy()
replay.slider.value = int(np.argmax(main.force))
assert replay.view.cursors[0].get_xdata()[0] == main.time[replay.slider.value]
paused_frame = replay.slider.value
replay.play.playing = True
replay.pause.click()
assert not replay.play.playing
assert replay.slider.value == paused_frame
assert replay.view.fig.get_figwidth() * replay.view.fig.dpi <= 1180.01
replay.reset.click()
assert replay.slider.value == 0
assert np.array_equal(before, main.u)

forecast_canvas = forecast.fig.canvas
for future_action in ['Slow press', 'Fast press', 'Hold', 'Release']:
    forecast.action.value = future_action
    forecast.button.click()
    assert forecast.last_error is None, repr(forecast.last_error)
    assert forecast.progress.value == 4
    assert forecast.fig.canvas is forecast_canvas
    assert future_action in forecast.fig._suptitle.get_text()
forecast.parent.value = matching['selected']['b']
forecast.action.value = 'Fast press'
forecast.noise.value = 1.
forecast.button.click()
assert forecast.last_error is None

sweep_canvas = sweep.fig.canvas
for excitation_name, noise_value in [('hold', 0.), ('hold', 1.), ('pulse', 0.), ('pulse', 1.)]:
    sweep.excitation.value = excitation_name
    sweep.noise.value = noise_value
    sweep.button.click()
    assert sweep.last_error is None, repr(sweep.last_error)
    assert sweep.progress.value == 7
    assert sweep.fig.canvas is sweep_canvas
print('PASS: slider cursor, pause, reset, bounded canvas, immutable main trace, four actions, two checkpoints, noise/excitation controls')
"""))
start = time.perf_counter()
NotebookClient(nb, timeout=600, kernel_name="nr-spatial-state", resources={"metadata": {"path": str(ROOT)}},
               store_widget_state=False).execute()
result = {"status": "passed", "wall_seconds": time.perf_counter()-start,
          "platform": sys.platform, "python": sys.executable,
          "scope": "Python widget callbacks and ipympl creation in a fresh kernel; not a frontend click test",
          "checks": ["shared replay cursor", "pause preserves frame", "reset", "bounded live canvas", "no trace mutation", "four future actions", "two checkpoints",
                     "noise selection", "excitation selection", "cached results"]}
write_json(args.record, result)
print(result)

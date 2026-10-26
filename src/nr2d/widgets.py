"""Native ipywidgets/ipympl views. Sliders replay; buttons launch computation."""
from pathlib import Path
from html import escape
import time

import ipywidgets as W
from IPython.display import display
import matplotlib.pyplot as plt
import numpy as np

from .physics import Trace
from .plotting import ReplayFigure, forecast_figure, sweep_figure
from .experiments import read_json, forecasts_for, sweep_for, load_histories


def table(headers, rows):
    css = 'style="padding:6px 12px;border-bottom:1px solid #ddd;text-align:left"'
    return "<table><thead><tr>"+"".join(f"<th {css}>{escape(str(v))}</th>" for v in headers)+"</tr></thead><tbody>"+"".join(
        "<tr>"+"".join(f"<td {css}>{escape(str(v))}</td>" for v in row)+"</tr>" for row in rows)+"</tbody></table>"


def checks_table(report):
    return W.HTML(table(["Physical check", "Measured error", "Limit", "Status"],
        [[r["check"], f"{r['error']:.3g} {r['unit']}", f"{r['tolerance']:.3g}", "PASS" if r["passed"] else "FAIL"]
         for r in report["rows"]]))


def matching_table(run):
    matching = read_json(Path(run)/"matching.json")
    histories = load_histories(run)
    a, b = [histories[matching["selected"][k]].observation[-1] for k in ("a", "b")]
    factors = [1e3, 1e3, 1e3, 1e6, 1e6]
    labels = ["Actual position (mm)", "Actual velocity (mm/s)", "Force (mN)", "Left lateral (um)", "Right lateral (um)"]
    rows = [[label, f"{x*s:.6g}", f"{y*s:.6g}", f"{abs(x-y)*s:.4g}", f"{tol*s:.4g}"]
            for label, x, y, s, tol in zip(labels, a, b, factors, matching["resolution_SI"])]
    return W.HTML(table(["Current observable", "A", "B", "Residual", "Resolution"], rows))


def figure_widget(fig):
    if isinstance(fig.canvas, W.Widget):
        # Bound only the live canvas; publication exports still use 300 dpi.
        width, height = fig.get_size_inches()
        fig.set_dpi(min(fig.dpi, 1180 / width, 650 / height))
        fig.canvas.toolbar_position = "bottom"
        fig.canvas.header_visible = False
        fig.canvas.layout.width = "100%"
        return fig.canvas
    output = W.Output()
    with output:
        display(fig)
    return output


class ReplayDashboard:
    def __init__(self, trace):
        with plt.ioff():
            self.view = ReplayFigure(trace)
        self.trace = trace
        self.slider = W.IntSlider(value=0, min=0, max=len(trace.time)-1, step=1,
                                  description="Frame", continuous_update=True, layout=W.Layout(width="60%"))
        self.play = W.Play(value=0, min=0, max=len(trace.time)-1, step=1, interval=120, show_repeat=True)
        self.link = W.jslink((self.play, "value"), (self.slider, "value"))
        self.pause = W.Button(description="Pause", icon="pause", layout=W.Layout(width="90px"))
        self.reset = W.Button(description="Reset", icon="undo", layout=W.Layout(width="90px"))
        self.status = W.HTML("REPLAY | use the timeline to inspect the trajectory.")
        self.slider.observe(self._changed, names="value")
        self.pause.on_click(self._pause)
        self.reset.on_click(self._reset)
        self.widget = W.VBox([W.HBox([self.play, self.pause, self.slider, self.reset]), self.status, figure_widget(self.view.fig)])

    def _changed(self, change):
        i = change["new"]
        self.view.update(i)
        self.status.value = f"<b>REPLAY</b> | t = {self.trace.time[i]:.2f} s | {escape(str(self.trace.phase[i]))}"

    def _pause(self, _):
        self.play.playing = False

    def _reset(self, _):
        self._pause(None)
        self.play.value = 0
        self.slider.value = 0


class ForecastDashboard:
    def __init__(self, run):
        self.run = Path(run)
        pair = read_json(self.run/"matching.json")["selected"]
        self.parent = W.Dropdown(options=[("History A", pair["a"]), ("History B", pair["b"])], description="Checkpoint")
        self.action = W.Dropdown(options=["Slow press", "Fast press", "Hold", "Release"], description="Future")
        self.noise = W.Dropdown(options=[("No noise", 0.), ("Nominal synthetic", 1.), ("4x synthetic", 4.)], description="Noise")
        self.force = W.Checkbox(value=False, description="Recompute", indent=False)
        self.button = W.Button(description="Run selected future", button_style="primary", icon="play", layout=W.Layout(width="200px"))
        self.progress = W.IntProgress(value=0, max=4, description="Progress")
        self.status = W.HTML()
        self.metrics = W.HTML()
        self.plot = W.VBox()
        self.fig = None
        self.last_error = None
        self.button.on_click(self._run)
        self.widget = W.VBox([W.HTML("Choose a checkpoint and future action, then run."),
                              W.HBox([self.parent, self.action, self.noise]), self.force,
                              W.HBox([self.button, self.progress]), self.status, self.plot, self.metrics])
        self._run(None)

    def _run(self, _):
        self.button.disabled = True
        self.progress.value = 0
        self.last_error = None
        start = time.perf_counter()
        self.status.value = "<b>RUNNING</b>"
        def progress(label):
            self.progress.value = min(3, self.progress.value+1)
            self.status.value = f"<b>RECOMPUTING</b>: {escape(label)}"
        try:
            predictions, metrics, mode = forecasts_for(self.run, self.parent.value, self.action.value, self.noise.value,
                                                        force=self.force.value, progress=progress)
            with plt.ioff():
                self.fig = forecast_figure(predictions, metrics, self.action.value, self.noise.value, fig=self.fig)
            # Reuse the live canvas: closing a displayed ipympl model before a
            # VBox update can leave a stale plot in VS Code's widget renderer.
            if not self.plot.children:
                self.plot.children = (figure_widget(self.fig),)
            self.fig.canvas.draw_idle()
            self.metrics.value = table(["Method", "Force RMSE (mN)", "Lateral RMSE (um)", "Inference (s)", "Fit status"],
                [[name, f"{m['force_rmse_N']*1e3:.4g}", f"{m['marker_rmse_m']*1e6:.4g}", f"{m['inference_seconds']:.3f}",
                  str(m["inference"].get("optimizer_success", "replay / reference"))] for name, m in metrics.items()])
            self.progress.value = 4
            self.status.value = f"<b>{mode}</b> | {time.perf_counter()-start:.2f} s"
        except Exception as exc:
            self.last_error = exc
            self.status.value = f"<b>FAILED</b>: {escape(str(exc))}"
        finally:
            self.button.disabled = False


class SweepDashboard:
    def __init__(self, run):
        self.run = Path(run)
        self.excitation = W.Dropdown(options=[("Smooth hold", "hold"), ("Loading pulse", "pulse")], description="Excitation")
        self.noise = W.Dropdown(options=[("No noise", 0.), ("Nominal synthetic", 1.), ("4x synthetic", 4.)], description="Noise")
        self.force = W.Checkbox(value=False, description="Recompute", indent=False)
        self.button = W.Button(description="Run history sweep", button_style="primary", icon="play", layout=W.Layout(width="200px"))
        self.progress = W.IntProgress(value=0, max=7, description="Windows")
        self.status = W.HTML()
        self.plot = W.VBox()
        self.fig = None
        self.last_error = None
        self.button.on_click(self._run)
        self.widget = W.VBox([W.HTML("Choose excitation and noise, then run. A new sweep takes about 20-60 s on CPU."),
                              W.HBox([self.excitation, self.noise]), W.HBox([self.button, self.force]),
                              self.progress, self.status, self.plot])
        self._run(None)

    def _run(self, _):
        self.button.disabled = True
        self.progress.value = 0
        self.last_error = None
        start = time.perf_counter()
        self.status.value = "<b>RUNNING</b>"
        def progress(label):
            self.progress.value = min(7, self.progress.value+1)
            self.status.value = f"<b>RECOMPUTING</b>: window {escape(label)} s."
        try:
            result, mode = sweep_for(self.run, self.excitation.value, self.noise.value, self.force.value, progress)
            with plt.ioff():
                self.fig = sweep_figure(result, fig=self.fig)
            if not self.plot.children:
                self.plot.children = (figure_widget(self.fig),)
            self.fig.canvas.draw_idle()
            self.progress.value = 7
            self.status.value = f"<b>{mode}</b> | {time.perf_counter()-start:.2f} s"
        except Exception as exc:
            self.last_error = exc
            self.status.value = f"<b>FAILED</b>: {escape(str(exc))}"
        finally:
            self.button.disabled = False

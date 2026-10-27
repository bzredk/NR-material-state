"""Draw the experiment procedure with the recorded pair of loading histories."""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/figures"
RUN = ROOT / "runs/2d_contact/pilot_c9dd23016896"
OUT.mkdir(parents=True, exist_ok=True)
matching = json.loads((RUN / "matching.json").read_text())
config = json.loads((RUN / "config.json").read_text())
parents = [matching["selected"][key] for key in ("a", "b")]

# Outlined SVG lettering avoids font substitution in GitHub's image viewer.
# The Python source remains editable; PDF retains embedded text.
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "path",
                     "pdf.fonttype": 42, "axes.unicode_minus": False})
fig = plt.figure(figsize=(12, 6.3), dpi=120, facecolor="#fafafa")
ax = fig.add_axes([0, 0, 1, 1])
ax.set(xlim=(0, 1200), ylim=(630, 0))
ax.set_axis_off()
INK, MUTED, BLUE = "#202124", "#63666b", "#326597"


def text(x, y, value, size=13, color=INK, weight="normal", **kwargs):
    ax.text(x, y, value, fontsize=size, color=color, weight=weight,
            va="top", linespacing=1.5, **kwargs)


def arrow(x1, y1, x2, y2, color="#a0a4a9"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->",
                                mutation_scale=12, color=color, linewidth=1.1))


text(42, 30, "2D contact experiment", 23, weight="bold")
text(42, 76, "Load", 14)
text(255, 76, "Hold", 14)
text(468, 76, "Release", 14)
text(705, 76, "Wait", 14)
text(918, 76, "Recontact", 14)
for start, end in ((113, 231), (328, 444), (572, 681), (775, 894)):
    arrow(start, 86, end, 86)
ax.plot([42, 1158], [124, 124], color="#dcdfe2", lw=.8)

text(42, 155, "Loading histories", 16, weight="bold")
text(447, 155, "State estimation", 16, weight="bold")
text(851, 155, "Future response", 16, weight="bold")
arrow(375, 167, 426, 167)
arrow(780, 167, 830, 167)

text(42, 196, "Different loads, matched endpoints", 11.5, MUTED)
trace_ax = fig.add_axes([.069, .435, .235, .188], facecolor="none")
colors = [BLUE, "#a35a73"]
source_files = [RUN / "matching.json", RUN / "config.json"]
for parent, letter, color in zip(parents, ("A", "B"), colors):
    path = RUN / "histories" / f"{parent}.npz"
    source_files.append(path)
    with np.load(path) as trace:
        trace_ax.plot(trace["time"] - trace["time"][-1], trace["d"] * 1e3,
                      color=color, lw=1.8, label=letter)
trace_ax.axvline(0, color="#959aa1", lw=.8, ls=":")
trace_ax.set(xlabel="Time before prediction (s)", ylabel="Tool position (mm)")
trace_ax.xaxis.label.set_size(10)
trace_ax.yaxis.label.set_size(10)
trace_ax.tick_params(labelsize=9, length=3, colors=MUTED)
trace_ax.set_xticks([-1.4, -.7, 0])
trace_ax.set_yticks([0, .2, .4])
for side in ("top", "right"):
    trace_ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    trace_ax.spines[side].set_color("#b7bbc0")
trace_ax.legend(frameon=False, fontsize=10, loc="upper right", ncol=2,
                handlelength=1.2, columnspacing=1)

text(42, 411, "Match position, velocity, force\nand both lateral markers.", 12)
residual_um = max(matching["selected"]["residual_SI"][3:]) * 1e6
tolerance_um = matching["resolution_SI"][3] * 1e6
text(42, 473, f"Lateral residual: {residual_um:.2f} µm (limit {tolerance_um:g} µm)", 10, MUTED)

text(447, 205, "Current measurements", 13)
text(447, 249, "0.2 s observation window", 13)
text(447, 293, "Full loading history", 13)
ax.plot([447, 755], [334, 334], color="#dcdfe2", lw=.8)
text(447, 354, "True internal state", 13, BLUE)
text(447, 382, "Simulation reference", 11, MUTED)
text(447, 443, "Repeat over window lengths,\nnoise levels and loading excitation.", 12)

text(851, 205, "Slow press", 13)
text(851, 243, "Fast press", 13)
text(851, 281, "Hold", 13)
text(851, 319, "Release", 13)
arrow(979, 359, 979, 398)
text(851, 413, "Compare predicted force\nand lateral displacement\nwith the continued simulation.", 12)

ax.plot([42, 1158], [518, 518], color="#dcdfe2", lw=.8)
text(42, 540, "All estimates use the same model for future prediction. Full replay knows the relaxed start.", 11, MUTED)
text(42, 574, f"Synthetic material: relaxation times {config['tau_fast']:.2f} s and {config['tau_slow']:.2f} s. "
     "Eight test histories.", 11, MUTED)

for suffix in ("svg", "png", "pdf"):
    metadata = {"Creator": "NR material state"}
    if suffix == "svg":
        metadata["Date"] = None
    fig.savefig(OUT / f"experiment_flow.{suffix}", dpi=220,
                facecolor=fig.get_facecolor(), metadata=metadata)
plt.close(fig)

source_files.append(Path(__file__).resolve())
provenance = {
    "run": RUN.relative_to(ROOT).as_posix(),
    "parents": parents,
    "trace": "Actual tool position; time relative to each history's endpoint.",
    "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in source_files},
}
(OUT / "experiment_flow.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
print(OUT / "experiment_flow.svg")

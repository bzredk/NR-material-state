"""Draw the current interaction-history / GRU / physical-state pipeline.

Schematic only; no simulated or empirical numerical results are plotted.
All graphics and exports use the saved Python backend.
"""

from pathlib import Path
import json
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.path import Path as MplPath
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parent
STEM = ROOT / "interaction_history_state_flow"
W, H = 1600, 900
INK = "#252A2E"
MID = "#677078"
LIGHT = "#CDD3D7"
STATE = "#386D85"
WHITE = "#FFFFFF"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial"],
    "font.size": 12,
    "mathtext.fontset": "custom",
    "mathtext.rm": "Arial",
    "mathtext.it": "Arial:italic",
    "mathtext.bf": "Arial:bold",
    "mathtext.sf": "Arial",
    "mathtext.fallback": None,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "figure.facecolor": WHITE,
    "savefig.facecolor": WHITE,
})

font_manager.findfont("Arial", fallback_to_default=False)
fig = plt.figure(figsize=(16, 9), dpi=300)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(H, 0)
ax.set_axis_off()
TEXTS = []


def text(x, y, label, size=12, color=INK, weight="normal", ha="left", va="center"):
    item = ax.text(x, y, label, fontsize=size, color=color, fontweight=weight,
                   ha=ha, va=va, linespacing=1.25, zorder=5)
    TEXTS.append(item)
    return item


def line(points, color=INK, lw=1.0, ls="-", z=2):
    xs, ys = zip(*points)
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, solid_capstyle="butt", zorder=z)


def arrow(points, color=INK, lw=1.0, ms=10):
    path = MplPath(points, [MplPath.MOVETO] + [MplPath.LINETO] * (len(points) - 1))
    ax.add_patch(FancyArrowPatch(path=path, arrowstyle="-|>", mutation_scale=ms,
                                linewidth=lw, color=color, fill=True, zorder=3,
                                capstyle="butt", joinstyle="miter"))


def box(x, y, w, h, edge=INK, lw=1.0):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=WHITE, edgecolor=edge,
                           linewidth=lw, zorder=1))


def spring(x, top, bottom, amplitude=8, turns=5):
    lead = 9
    points = [(x, top), (x, top + lead)]
    span = bottom - top - 2 * lead
    for i in range(2 * turns):
        points.append((x + (amplitude if i % 2 == 0 else -amplitude),
                       top + lead + span * (i + .5) / (2 * turns)))
    points.extend([(x, bottom - lead), (x, bottom)])
    line(points, lw=1.0)


def dashpot(x, top, bottom):
    # Open-top cylinder, horizontal piston and connected lower rod.
    piston = top + 24
    base = bottom - 13
    line([(x, top), (x, piston)], lw=1.0)
    line([(x - 14, piston), (x + 14, piston)], lw=1.0)
    line([(x - 19, top + 13), (x - 19, base), (x + 19, base),
          (x + 19, top + 13)], lw=1.0)
    line([(x, base), (x, bottom)], lw=1.0)


# Main argument: one decision from observed history.
text(60, 62, "From interaction history to action", size=25, weight="bold")
text(60, 104, "GRU state estimation with a fixed physical model", size=14, color=MID)

# Direct current-observation inputs to the constrained head and the rollout.
line([(175, 285), (175, 208), (1067, 208)], color=MID, lw=.9)
arrow([(752, 208), (752, 285)], color=MID, lw=.9)
arrow([(1067, 208), (1067, 285)], color=MID, lw=.9)
ax.plot([752], [208], "o", color=MID, ms=2.4, zorder=4)
text(590, 186, r"Current observation: $x_t,\ v_t,\ F_t$", size=12, color=MID, ha="center")

# Future actions are independent rollout inputs, not history-encoder inputs.
text(1402, 171, "Candidate commands", size=13, ha="center")
text(1402, 200, r"$u^{(j)}$   and controller $K, D$", size=12, ha="center", color=MID)
arrow([(1265, 191), (1225, 191), (1225, 315), (1190, 315)], color=MID, lw=.9)

blocks = [(60, 230), (355, 205), (630, 245), (945, 245), (1265, 275)]
for x, w in blocks:
    box(x, 285, w, 120)

text(175, 313, "Interaction history", size=16, weight="bold", ha="center")
text(175, 348, r"$H_t=\{x,v,F,u,\Delta t\}_{t-H:t}$", size=12, ha="center")
text(175, 379, "3 seconds / 301 samples", size=11, color=MID, ha="center")

text(457.5, 313, "GRU encoder", size=17, weight="bold", ha="center")
text(457.5, 348, "Recurrent memory", size=12, color=MID, ha="center")
text(457.5, 379, r"$h_t$ (32 dimensions)", size=12, ha="center")

text(752.5, 313, "State estimate", size=16, weight="bold", ha="center")
text(752.5, 348, "Head + physical constraint", size=11, color=MID, ha="center")
text(752.5, 379, r"$\hat{z}_t=(\hat{z}_{1,t},\hat{z}_{2,t})$", size=14, color=STATE, ha="center")

text(1067.5, 313, "Physics rollout", size=16, weight="bold", ha="center")
text(1067.5, 348, "Fixed material law", size=12, color=MID, ha="center")
text(1067.5, 379, r"$\hat{s}_0=(x_t,v_t,\hat{z}_t)$", size=13, ha="center")

text(1402.5, 313, "Action selection", size=16, weight="bold", ha="center")
text(1402.5, 348, "Respect the force limit", size=12, color=MID, ha="center")
text(1402.5, 379, "Minimize completion time", size=12, ha="center")

arrow([(290, 345), (355, 345)])
arrow([(560, 345), (630, 345)])
arrow([(875, 345), (945, 345)], color=STATE, lw=1.4)
arrow([(1190, 367), (1265, 367)])
text(1228, 345, r"$\hat{x},\hat{F}$", size=12, color=MID, ha="center")

# Physical interaction inset; true material state remains in the plant.
text(60, 483, "Simulated interaction", size=15, weight="bold")
text(60, 511, "1D contact / two material states", size=11, color=MID)

box(65, 550, 145, 42, edge=MID, lw=.9)
text(137.5, 564, "Impedance", size=11, ha="center")
text(137.5, 581, r"$K, D$", size=11, color=MID, ha="center")
arrow([(210, 571), (250, 571)], color=INK, lw=.9, ms=8)
box(250, 550, 105, 42, lw=1.0)
text(302.5, 571, r"Head $m$", size=12, ha="center")
line([(302.5, 592), (302.5, 619)], lw=1.0)
line([(100, 619), (350, 619)], lw=1.2)
text(368, 618, r"$x, v, F$", size=11, color=MID)

spring(110, 619, 766, amplitude=8, turns=7)
text(80, 693, r"$k_\infty$", size=12, ha="right")
line([(110, 766), (110, 787)], lw=1.0)

for x, branch in [(230, 1), (350, 2)]:
    spring(x, 619, 693, amplitude=7, turns=4)
    text(x + 20, 653, rf"$k_{branch}$", size=11)
    dashpot(x, 693, 766)
    line([(x, 766), (x, 787)], lw=1.0)
    text(x + 29, 714, rf"$\eta_{branch}$", size=11, color=MID)
    text(x + 29, 747, rf"$z_{branch}$", size=13, color=STATE)

line([(90, 787), (370, 787)], lw=1.1)
for x in range(95, 371, 15):
    line([(x, 787), (x - 8, 798)], color=MID, lw=.65)
text(230, 819, r"True material state: $z_t=(z_1,z_2)$", size=11, color=STATE, ha="center")

# Observations, not privileged states, enter the encoder.
arrow([(355, 570), (435, 570), (435, 454), (175, 454), (175, 405)], color=MID, lw=.9)
text(306, 434, r"Measurements $x,v,F$", size=11, color=MID, ha="center")

# Rollout expansion: the same inferred initial state is advanced for every candidate.
line([(520, 485), (1540, 485)], color=LIGHT, lw=.7)
text(520, 516, "Inside each physics rollout", size=15, weight="bold")
text(520, 547, "Every candidate starts from the same estimated state.", size=12, color=MID)

centers = [670, 1040, 1410]
titles = ["Initial state", "Predicted state", "Predicted state"]
symbols = [r"$\hat{s}_0$", r"$\hat{s}_1$", r"$\hat{s}_2$"]
motions = [r"$x_t,\ v_t$", r"$\hat{x}_1,\ \hat{v}_1$", r"$\hat{x}_2,\ \hat{v}_2$"]
memories = [r"$\hat{z}_{1,t},\ \hat{z}_{2,t}$", r"$\hat{z}_{1,t+1},\ \hat{z}_{2,t+1}$", r"$\hat{z}_{1,t+2},\ \hat{z}_{2,t+2}$"]

for cx, title, symbol, motion, memory in zip(centers, titles, symbols, motions, memories):
    text(cx, 591, title, size=11, color=MID, ha="center")
    text(cx, 625, symbol, size=19, ha="center")
    text(cx, 668, motion, size=13, ha="center")
    text(cx, 705, memory, size=14, color=STATE, ha="center")
    line([(cx - 105, 646), (cx + 105, 646)], color=LIGHT, lw=.6)

for x1, x2, j in [(centers[0], centers[1], 0), (centers[1], centers[2], 1)]:
    arrow([(x1 + 114, 671), (x2 - 114, 671)], color=STATE, lw=1.1)
    text((x1 + x2) / 2, 639, r"$f_{\mathrm{phys}}$", size=12, color=STATE, ha="center")
    text((x1 + x2) / 2, 704, rf"$u_{{{j}}}^{{(j)}}$", size=11, color=MID, ha="center")

text(520, 759, "Material-state components are highlighted in blue.",
     size=10.5, color=MID)

# The selected command returns to the physical controller for execution.
arrow([(1402.5, 405), (1564, 405), (1564, 853), (25, 853), (25, 571), (65, 571)],
      color=INK, lw=.9, ms=10)
text(980, 830, r"Execute selected command $u^*$", size=12, ha="center")
text(60, 883, "One decision at time t: infer state, compare candidate futures, then execute.",
     size=10, color=MID)

fig.canvas.draw()
renderer = fig.canvas.get_renderer()
outside = []
for artist in TEXTS:
    bb = artist.get_window_extent(renderer)
    if bb.x0 < 0 or bb.x1 > fig.bbox.width or bb.y0 < 0 or bb.y1 > fig.bbox.height:
        outside.append(artist.get_text())
if outside:
    raise RuntimeError(f"Text outside canvas: {outside}")

fig.savefig(STEM.with_suffix(".svg"))
fig.savefig(STEM.with_suffix(".pdf"))
fig.savefig(STEM.with_suffix(".png"), dpi=300)
plt.close(fig)

svg = ET.parse(STEM.with_suffix(".svg"))
ns = {"svg": "http://www.w3.org/2000/svg"}
editable_text = len(svg.findall(".//svg:text", ns))
assert editable_text >= 40, editable_text

report = {
    "canvas_inches": [16, 9],
    "png_pixels": [4800, 2700],
    "font": "Arial",
    "backend": "Python / matplotlib",
    "text_outside_canvas": outside,
    "svg_editable_text_elements": editable_text,
    "diagram_scope": "one history-conditioned decision, not a closed-loop performance claim",
    "visual_review": "No text overlaps; arrows and labels readable; consistent Arial; state components distinct from GRU memory.",
    "exports": [STEM.with_suffix(ext).name for ext in (".svg", ".pdf", ".png")],
}
(ROOT / "render_checks.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))

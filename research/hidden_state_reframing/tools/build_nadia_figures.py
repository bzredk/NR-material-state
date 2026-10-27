"""Reconstruct archived evidence and a proposed decision schematic; no simulations."""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

PLAN = Path(__file__).resolve().parents[1]
REPO = PLAN.parents[1]
OUT = PLAN / "figures"
OUT.mkdir(exist_ok=True)
DATA = json.loads((PLAN / "figure_data.json").read_text(encoding="utf-8"))
BLUE, ORANGE, GREEN, GREY = "#176b97", "#c45b26", "#267a65", "#52616b"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "savefig.facecolor": "white"})


def save(fig, stem):
    for suffix in ("png", "svg"):
        fig.savefig(OUT / f"{stem}.{suffix}", dpi=180, bbox_inches="tight")
    plt.close(fig)


def aliasing():
    path = REPO / "1D/experiments/history_dependence/runs/round2_v1/data/test_wait.npz"
    d = np.load(path)
    i = 0  # Fixed by index, never selected by effect magnitude.
    h, z = d["history"][i], d["oracle_z"][i]
    assert np.allclose(d["commands"][i, 0], d["commands"][i, 1])
    fig, ax = plt.subplots(2, 2, figsize=(12.5, 8.4))
    fig.subplots_adjust(hspace=.42, wspace=.36, top=.88, bottom=.13)
    fig.suptitle("1 | Same current readings, different internal composition", fontsize=17, x=.06, ha="left")
    fig.text(.06, .922, "ARCHIVED 1D simulation | E1 test_wait, pair index 0 | illustrative pair, not a new experiment", color=GREY)
    t = (np.arange(h.shape[1]) - h.shape[1] + 1) * .01
    for j, color in enumerate((BLUE, ORANGE)):
        ax[0, 0].plot(t, 1000*h[j, :, 3], color=color, label=f"History {chr(65+j)}")
    ax[0, 0].set(title="Feasible recorded loading histories", xlabel="Time before prediction cut (s)", ylabel="Issued reference (mm)")
    ax[0, 0].legend(frameon=False)
    ax[0, 1].axis("off")
    current = h[:, -1, :4]
    text = "Current delivered observations at cut\n\n"
    for name, value, unit in zip(("Displacement", "Velocity", "Contact force", "Command"), current[0]*[1000,1000,1,1000], ("mm", "mm/s", "N", "mm")):
        text += f"{name:15s}  {value:.4f} {unit}\n"
    text += "\nA and B are byte-identical here.\nArchived noise was coupled across the pair.\nNew protocol requires independent noise\nand sensor-resolution matching."
    ax[0, 1].text(0, .98, text, va="top", fontsize=11, linespacing=1.5, family="DejaVu Sans Mono")
    x = np.arange(2)
    for j, color in enumerate((BLUE, ORANGE)):
        ax[1, 0].bar(x + (j-.5)*.3, 1000*z[j], .3, color=color, label=f"History {chr(65+j)}")
    ax[1, 0].set(xticks=x, xticklabels=("Fast branch", "Slow branch"), ylabel="True dashpot extension (mm)", title="Evaluation-only internal variables")
    future_t = (np.arange(d["truth"].shape[2])+1)*.01
    for j, color in enumerate((BLUE, ORANGE)):
        ax[1, 1].plot(future_t, d["truth"][i, j, :, 2], color=color, label=f"Force {chr(65+j)}")
    ax[1, 1].set(xlabel="Time after prediction cut (s)", ylabel="True force (N)", title="Identical future commands")
    secondary = ax[1, 1].twinx()
    secondary.plot(future_t, d["truth"][i, 0, :, 2]-d["truth"][i, 1, :, 2], color=GREY, linestyle=":", label="A minus B")
    secondary.set_ylabel("Force difference A - B (N)", color=GREY)
    ax[1, 1].legend(frameon=False, loc="upper left")
    secondary.legend(frameon=False, loc="upper right")
    fig.text(.06, .035, "Scope: one fixed two-mode plant; hidden-state-directed history construction is a privileged mechanism diagnostic.\nThis figure establishes neither natural prevalence nor decision benefit. Pair index was fixed without selecting future effects.", fontsize=10, color=GREY)
    save(fig, "01_state_aliasing")
    return {"path": str(path.relative_to(REPO)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "pair_index": i, "pair_id": int(d["pair_ids"][i])}


def existing():
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.8), gridspec_kw={"width_ratios": [1.15,1,1.05]})
    fig.subplots_adjust(top=.77, bottom=.24, wspace=.42)
    fig.suptitle("2 | What the existing evidence supports - and limits", x=.055, ha="left", fontsize=17)
    fig.text(.055, .88, "ARCHIVED results, reanalyzed | No new training or control trial | Independent units are history pairs", color=GREY)
    vals = DATA["e1"]["values"]
    means = np.array([v["mean"] for v in vals])
    errors = np.array([[v["mean"]-v["ci_low"] for v in vals], [v["ci_high"]-v["mean"] for v in vals]])
    axes[0].barh(np.arange(4), means, xerr=errors, color=[GREEN, BLUE, ORANGE, GREY], capsize=3)
    axes[0].set(yticks=np.arange(4), yticklabels=["Full classical", "Local 0.2 s", "History 3 s", "Snapshot"], xscale="log", xlabel="Future-force RMSE (N), lower is better", title="E1: a neural method is not yet justified")
    axes[0].invert_yaxis()
    for j, m in enumerate(means):
        axes[0].text(m*1.3, j, f"{m:.5f}", va="center", fontsize=9)
    axes[0].set_xlim(1e-4,.2)
    for v, col in zip(DATA["e3_state_error"]["values"], (GREEN,ORANGE,BLUE)):
        axes[1].plot([0,1], [v["rmse_mm_at_cut"],v["rmse_mm_at_handoff"]], "o-", color=col, label=v["label"], lw=2)
    axes[1].set(yscale="log", xticks=[0,1], xticklabels=["Initial cut", "After 0.3 s\ncommon release"], ylabel="Internal-state RMSE (mm)", title="E3: convergence can overwrite accuracy")
    axes[1].legend(frameon=False)
    axes[2].bar([0,1], [100,84.8958333333], color=[GREY, ORANGE], width=.6)
    axes[2].set(ylim=(0,115), xticks=[0,1], xticklabels=["Task window", "Including\nshared prefix"], ylabel="Constraint-respecting success (%)", title="E3: no useful history action gain")
    for j, v in enumerate([100,84.8958333333]):
        axes[2].text(j,v+3,f"{v:.2f}%",ha="center",weight="bold")
    fig.text(.055, .105, "E1: 192 pairs, fixed plant; archived intervals.    E3 state trace: seed 11, 64 pairs.    E3 outcomes: 3,456 dependent branches/method, 64 pairs.", fontsize=9, color=GREY)
    fig.text(.055, .055, "History - snapshot: 0 percentage-point task success gain; cost gain -2.89 microseconds. No true-state action-reference batch was run.\nA degenerate [0,0] bootstrap interval is not equivalence; 522 prefix cap breaches must remain in full-operation accounting.", fontsize=10, color=GREY)
    save(fig, "02_existing_evidence")


def decision():
    fig, ax = plt.subplots(figsize=(13,8.6))
    ax.set(xlim=(0,1), ylim=(0,1)); ax.axis("off")
    fig.suptitle("3 | The next experiment separates four explanations", x=.06, ha="left", fontsize=17)
    fig.text(.06,.92,"PROPOSED decision schematic | These branches are not observed results",color=GREY)

    def box(x,y,w,h,title,body,color):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.012",facecolor=color,edgecolor="#ccd6dd",linewidth=1))
        ax.text(x+.014,y+h-.022,title,va="top",weight="bold",fontsize=11)
        ax.text(x+.014,y+h-.073,body,va="top",fontsize=10,linespacing=1.55)

    box(.03,.78,.94,.16,"First: establish a physical information gap (X01-X05)","Feasible histories; match every deployable current channel; independent noise; common future commands.\nCompare snapshot, short/full classical observer, recursive state, and true-state reference.","#eaf3f7")
    box(.03,.45,.44,.23,"Case 1 | Relevant response, unnecessary state","True-state access has no useful task advantage.\nCheck action-library sensitivity and success ceiling.\nKeep a scoped prediction claim; do not invent urgency.","#f3f4f5")
    box(.53,.45,.44,.23,"Case 2 | Useful, but information is inadequate","True-state reference helps; current sensing/history\nleaves action-relevant ambiguity. Validate this beyond\none failed learner; test a probe, sensor, or belief.","#fff3e9")
    box(.03,.14,.44,.23,"Case 3 | Feedback supplies information in time","History helps initially, but ordinary feedback removes\nthe decision gap. Require genuine accuracy recovery;\nobserver overwrite is a separate confound.","#edf6ed")
    box(.53,.14,.44,.23,"Case 4 | Useful and inferable; estimator loses it","Reference headroom and usable information remain.\nTarget the failed inference/update mechanism.\nThis identifies a specific method-development need.","#e9f1fb")
    ax.text(.5,.725,"Fixed task + action set + controller + credible feedback + full-operation constraints",ha="center",fontsize=10,color=GREY)
    ax.text(.5,.06,"Then: spatial 2D evidence -> qualified articulated 3D manipulation -> real robot",ha="center",weight="bold",fontsize=12)
    fig.text(.06,.025,"True-state access is a restricted information reference, not a global optimal-control upper bound. Cases may coexist across histories.",fontsize=10,color=GREY)
    save(fig,"03_decision_gate")


if __name__ == "__main__":
    source = aliasing()
    existing()
    decision()
    metadata = {"status":"archived_evidence_and_proposed_schematic_only", "pair_source":source,
                "figure_data_sha256":hashlib.sha256((PLAN/"figure_data.json").read_bytes()).hexdigest(),
                "outputs":[p.name for p in sorted(OUT.glob("*")) if p.suffix in (".png",".svg")]}
    (OUT/"provenance.json").write_text(json.dumps(metadata,indent=2)+"\n",encoding="utf-8")
    print("Wrote three figures in PNG/SVG; no experiment executed.")

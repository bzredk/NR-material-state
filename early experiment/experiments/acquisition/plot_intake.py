"""Raw-response diagnostics before model fitting; selection is condition-based."""
import argparse
import os
from pathlib import Path
from prepare_collection import ROOT, read_json, read_csv, write_json, fresh_output
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.family":"sans-serif", "font.sans-serif":["Arial","DejaVu Sans"],
                     "font.size":8, "axes.spines.top":False, "axes.spines.right":False,
                     "svg.fonttype":"none", "pdf.fonttype":42})
COLORS = ["#287DA8", "#B56736", "#47907E", "#8A6CA8"]


def save(fig, out, name, label):
    fig.text(.08, .015, label, fontsize=6, color="#454B52")
    fig.tight_layout(rect=(0,.045,1,.97))
    for ext in ["png","svg","pdf"]:
        fig.savefig(out / (name+"."+ext), dpi=300)
    plt.close(fig)


def main(inspected, output):
    folder = Path(inspected); out = fresh_output(output)
    meta = read_json(folder / "source/metadata.json")
    rows = read_csv(folder / "normalized_with_context.csv")
    manifest = read_csv(folder / "source/episodes.csv")
    available = {(r["session_id"],r["episode_id"]) for r in rows}
    eligible = [e for e in manifest if (e["session_id"],e["episode_id"]) in available
                and e.get("role","core") == "core" and e.get("amplitude_m") and e.get("wait_s")]
    if not eligible:
        raise ValueError("Need at least one recorded core episode with declared amplitude and wait")
    priority = sorted(eligible, key=lambda e: (e["program"]!="overshoot", -float(e["amplitude_m"]),
                                             float(e["wait_s"]), int(e.get("repeat") or 1)))[0]
    selection = [e for e in eligible if all(e[k] == priority[k] for k in ["program","amplitude_m","wait_s"])]
    source = "REAL RECORDINGS" if meta["data_type"] == "real" else "REUSED SYNTHETIC SOFTWARE FIXTURE — NO REAL MATERIAL DATA"
    fig, axes = plt.subplots(3,1, figsize=(7.2,6.1))
    for j, e in enumerate(selection):
        rr = [r for r in rows if (r["session_id"],r["episode_id"]) == (e["session_id"],e["episode_id"])]
        t = np.array([float(r["timestamp_s"]) for r in rr]); t -= t[0]
        x = np.array([float(r["actual_position_m"]) for r in rr])*1000
        u = np.array([float(r["command_position_m"]) for r in rr])*1000
        f = np.array([float(r["normal_force_N"]) for r in rr])
        c = COLORS[j % len(COLORS)]; label = "Repeat "+e.get("repeat","?")
        axes[0].plot(t,x,color=c,label=label+" actual")
        axes[0].plot(t,u,"--",color=c,alpha=.65,label=label+" command")
        axes[1].plot(t,f,color=c,label=label)
        axes[2].plot(x,f,color=c,label=label)
        if j == 0:
            phases = np.array([r["phase"] for r in rr])
            for i, phase in enumerate(dict.fromkeys(phases)):
                idx = np.flatnonzero(phases==phase)
                for ax in axes[:2]:
                    ax.axvspan(t[idx[0]], t[idx[-1]], color="#CBD6DF", alpha=.12 if i%2 else .3, zorder=-1)
                axes[0].text((t[idx[0]]+t[idx[-1]])/2, 1.02, phase, rotation=30, ha="center",
                             transform=axes[0].get_xaxis_transform(), fontsize=6)
    axes[0].set(xlabel="Episode time (s)", ylabel="Position (mm)")
    axes[1].set(xlabel="Episode time (s)", ylabel="Normal force (N)")
    axes[2].set(xlabel="Actual position (mm)", ylabel="Normal force (N)")
    for ax in axes:
        ax.grid(alpha=.15); ax.legend(fontsize=6, ncol=2, loc="best")
    fig.suptitle("Raw history and recontact: predeclared priority condition", fontsize=10)
    save(fig,out,"01_raw_interaction", source+" | all available repeats of the chosen condition; no peak alignment")
    features = read_csv(folder / "episode_observables.csv")
    entries = {(e["session_id"],e["episode_id"]):e for e in eligible}
    core = [r for r in features if (r["session_id"],r["episode_id"]) in entries]
    conditions = sorted({(r["program"],float(r["amplitude_m"])) for r in core})
    fig, axes = plt.subplots(1,3,figsize=(7.2,3.0))
    fields = ["threshold_contact_m","recontact_peak_N","recontact_impulse_Ns"]
    labels = ["Threshold contact (mm)","Peak force (N)","Recontact impulse (N s)"]
    for ci, (program,amp) in enumerate(conditions):
        for rep in sorted({r["repeat"] for r in core}):
            group = sorted([r for r in core if r["program"]==program and float(r["amplitude_m"])==amp and r["repeat"]==rep],
                           key=lambda r:float(r["wait_s"]))
            for ax, field, ylabel in zip(axes,fields,labels):
                valid = [r for r in group if r.get(field) not in [None,""]]
                if valid:
                    ax.plot([float(r["wait_s"]) for r in valid],
                            [float(r[field])*(1000 if field=="threshold_contact_m" else 1) for r in valid],
                            "o-" if str(rep)=="1" else "s--", color=COLORS[ci%len(COLORS)],
                            markersize=3, linewidth=.8, label=f"{program}, {amp*1000:g} mm" if str(rep)=="1" else None)
                ax.set(xlabel="Planned wait (s)",ylabel=ylabel)
                ax.grid(alpha=.15)
    if conditions:
        axes[1].legend(fontsize=5.5,loc="best")
    fig.suptitle("Waiting changes the next interaction: complete recorded grid",fontsize=10)
    save(fig,out,"02_wait_effect_raw", source+" | individual technical repeats; not population confidence intervals")
    write_json(out / "figure_manifest.json", dict(data_type=meta["data_type"],
               source=str(folder.resolve()), selected_episode_ids=[e["episode_id"] for e in selection],
               rule="overshoot, highest amplitude, shortest wait; all available repeats",
               scientific_questions=["Are commands, motion and force coherent through detachment/recontact?",
                                     "Does waiting change observable recontact consequences across the full grid?"],
               limitations="Threshold contact is not free-surface height. These plots make no mechanism or action-value claim."))
    print(out)


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("inspected");p.add_argument("--output",required=True)
    a=p.parse_args();main(a.inspected,a.output)

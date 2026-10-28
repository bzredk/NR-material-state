"""Matplotlib figures shared by the notebook, widgets and command-line exports."""
from pathlib import Path
import time

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle
import numpy as np

from .physics import Config, SpatialModel, Trace
from .estimators import METHODS, COLORS
from .experiments import ROOT, read_json, write_json, load_histories, forecasts_for, sweep_for, source_hashes

PAIR_COLORS = ["#275D9B", "#AE4774"]
PHASE_COLORS = ["#CCE0EF", "#D2E6DA", "#F0D8CB", "#E5DDF2", "#CCE0EF", "#D2E6DA", "#F0D8CB"]


def style():
    mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.titlesize": 14,
                         "axes.labelsize": 12, "legend.fontsize": 10, "xtick.labelsize": 10,
                         "ytick.labelsize": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.alpha": .17, "figure.dpi": 110,
                         "savefig.dpi": 300, "svg.fonttype": "none", "pdf.fonttype": 42})


def phase_bands(ax, trace, labels=False):
    boundaries = np.r_[1, np.flatnonzero(trace.phase[1:] != trace.phase[:-1])+1, len(trace.time)]
    boundaries = sorted(set(boundaries))
    for i, (a, b) in enumerate(zip(boundaries[:-1], boundaries[1:])):
        lo, hi = trace.time[max(0, a-1)], trace.time[min(b-1, len(trace.time)-1)]
        ax.axvspan(lo, hi, color=PHASE_COLORS[i % len(PHASE_COLORS)], alpha=.35, lw=0, zorder=0)
        if labels:
            ax.text((lo+hi)/2, 1.015, str(trace.phase[a]), ha="center", va="bottom",
                    transform=ax.get_xaxis_transform(), fontsize=9)


def internal_field(trace, index=-1):
    # Dimensionless tensor norm; privileged simulator diagnosis, not a sensor.
    z = trace.z[index, 1]
    return np.sqrt(z[:, 0]**2+z[:, 1]**2+z[:, 2]**2/2)


def body_panel(ax, model, trace, index, vmax=None):
    nodes = model.nodes+trace.u[index].reshape(-1, 2)
    field = internal_field(trace, index)
    mesh = PolyCollection(nodes[model.tri]*1e3, array=field, cmap="magma", edgecolors="#646464",
                          linewidths=.22, clim=(0, vmax or max(float(field.max()), 1e-5)))
    ax.add_collection(mesh)
    c = model.c
    tool = Circle((0, (c.height+c.radius-trace.d[index])*1e3), c.radius*1e3,
                  facecolor="#B8C3CE", edgecolor="#43566D", linewidth=1.5, zorder=3)
    ax.add_patch(tool)
    markers = ax.scatter(*nodes[model.marker_nodes].T*1e3, s=70, c="#16B9B1", edgecolors="white", zorder=5)
    _, _, _, gap, points, _ = model.contact(trace.u[index], trace.d[index])
    contact = ax.scatter(*(points[gap>0]*1e3).T, s=30, c="#EE743B", zorder=6, label="Contact quadrature")
    ax.plot([-c.width*500, c.width*500], [0, 0], color="#26344A", lw=4)
    ax.set(xlim=(-c.width*550, c.width*550), ylim=(-1, c.height*1e3+3),
           xlabel="x (mm)", ylabel="y (mm)", aspect="equal")
    ax.grid(False)
    return mesh, tool, markers, contact


class ReplayFigure:
    """A cheap time-cursor update; never runs the physical solver."""
    def __init__(self, trace):
        style()
        self.trace = trace
        self.model = SpatialModel(Config(**trace.config))
        self.fig = plt.figure(figsize=(14, 7.4), layout="constrained")
        grid = self.fig.add_gridspec(3, 2, width_ratios=(1.05, 1.65))
        self.ax_body = self.fig.add_subplot(grid[:, 0])
        self.axes = [self.fig.add_subplot(grid[i, 1]) for i in range(3)]
        vmax = max(float(np.sqrt(np.sum(trace.z[:, 1, :, :2]**2, axis=-1)+trace.z[:, 1, :, 2]**2/2).max()), 1e-5)
        self.mesh, self.tool, self.markers, self.contact = body_panel(self.ax_body, self.model, trace, 0, vmax)
        self.fig.colorbar(self.mesh, ax=self.ax_body, orientation="horizontal", shrink=.85, pad=.10,
                          label="Slow internal strain norm (truth)")
        self.caption = self.ax_body.text(.02, .99, "", transform=self.ax_body.transAxes, va="top", fontsize=11,
                                         bbox=dict(facecolor="white", alpha=.85, edgecolor="none"), zorder=9)
        a, b, d = self.axes
        a.plot(trace.time, trace.force, color=COLORS["True state"], lw=2.3, label="Contact reaction")
        a.set_ylabel("Force (N)")
        a.legend(loc="upper right")
        b.plot(trace.time, trace.command*1e3, "--", c="#7B8A99", lw=1.6, label="Command")
        b.plot(trace.time, trace.d*1e3, c="#275D9B", lw=2, label="Actual tool")
        b.set_ylabel("Indentation (mm)")
        b.legend(loc="upper right", ncol=2)
        d.plot(trace.time, trace.markers[:, 0]*1e6, c="#167A70", lw=2, label="Left outward")
        d.plot(trace.time, trace.markers[:, 1]*1e6, "--", c="#AA713D", lw=1.7, label="Right outward")
        d.set(ylabel="Lateral motion (um)", xlabel="Time (s)")
        d.legend(loc="upper right", ncol=2)
        self.cursors = []
        for j, ax in enumerate(self.axes):
            phase_bands(ax, trace, labels=j==0)
            ax.set_xlim(trace.time[0], trace.time[-1])
            self.cursors.append(ax.axvline(trace.time[0], color="#C04A32", lw=1.4))
        self.fig.suptitle("Spatial 2D contact | synthetic material | physical deformation at 1x scale", fontsize=15)
        self.update(0)

    def update(self, index):
        index = int(index)
        tr, m = self.trace, self.model
        nodes = m.nodes+tr.u[index].reshape(-1, 2)
        self.mesh.set_verts(nodes[m.tri]*1e3)
        self.mesh.set_array(internal_field(tr, index))
        self.tool.center = (0, (m.c.height+m.c.radius-tr.d[index])*1e3)
        self.markers.set_offsets(nodes[m.marker_nodes]*1e3)
        _, _, _, gap, pts, _ = m.contact(tr.u[index], tr.d[index])
        self.contact.set_offsets(pts[gap>0]*1e3)
        self.caption.set_text(f"t = {tr.time[index]:.2f} s | {tr.phase[index]}\nF = {tr.force[index]:.3f} N\n"
                              f"v = {tr.v[index]*1e3:.2f} mm/s\nActive contact points: {np.count_nonzero(gap>0)}")
        for line in self.cursors:
            line.set_xdata([tr.time[index], tr.time[index]])
        self.fig.canvas.draw_idle()
        return self.mesh, self.tool, self.markers, self.contact, self.caption, *self.cursors


def paired_figure(run):
    style()
    run = Path(run)
    matching = read_json(run/"matching.json")
    chosen = matching["selected"]
    histories = load_histories(run)
    a, b = [histories[chosen[k]] for k in ("a", "b")]
    fig, axes = plt.subplots(2, 3, figsize=(16, 8.4), layout="constrained")
    vmax = max(float(internal_field(a).max()), float(internal_field(b).max()))
    for j, (label, tr, color) in enumerate(zip(("A", "B"), (a, b), PAIR_COLORS)):
        ax = axes[0, j]
        ax.plot(tr.time, tr.command*1e3, "--", c="#86919C", lw=1.5, label="Command")
        ax.plot(tr.time, tr.d*1e3, c=color, lw=2, label="Actual tool")
        ax.set(xlabel="Time (s)", ylabel="Indentation (mm)", title=f"History {label}: {tr.metadata['parent_id']}")
        ax.axvline(tr.time[-1], c="#C04A32", ls=":", lw=2)
        ax.legend(loc="upper right", fontsize=9)
        model = SpatialModel(Config(**tr.config))
        mesh, *_ = body_panel(axes[1, j], model, tr, -1, vmax)
        axes[1, j].set_title(f"{label}: hidden slow field at prediction cut")
    fig.colorbar(mesh, ax=list(axes[1, :2]), orientation="horizontal", shrink=.65,
                 label="Slow internal strain norm (truth)", pad=.1)
    ax = axes[0, 2]
    ax.barh(["Actual position", "Actual velocity", "Total force", "Left lateral", "Right lateral"],
            chosen["normalized_residual"], color="#657AA4")
    ax.axvline(1, ls="--", color="#C04A32", label="Acceptance threshold")
    ax.set(xlabel="Absolute residual / sensor resolution", xlim=(0, max(1.15, max(chosen["normalized_residual"])*1.1)),
           title=f"Current-observation match: {'PASS' if chosen['accepted'] else 'FAIL'}")
    ax.invert_yaxis(); ax.legend(loc="lower right")
    fa, fb = [Trace.load(run/"pair_refinement"/f"default_{chosen[k]}.npz") for k in ("a", "b")]
    ax = axes[1, 2]
    for label, tr, color in zip(("A", "B"), (fa, fb), PAIR_COLORS):
        ax.plot(tr.time-tr.time[0], tr.force, c=color, lw=2, label=f"History {label}")
    ax.set(xlabel="Time after prediction cut (s)", ylabel="Force (N)", title="Identical future command: slow press")
    ax.legend(loc="upper left")
    inset = ax.inset_axes([.48, .17, .48, .30])
    inset.plot(fa.time-fa.time[0], (fa.force-fb.force)*1e3, c="#7F375A", lw=1.5)
    inset.set_title("A - B (mN)", fontsize=10)
    inset.tick_params(labelsize=8)
    fig.suptitle(f"Matched histories | accepted {matching['accepted']}/{matching['attempted']}", fontsize=15)
    return fig


def forecast_figure(predictions, metrics, action="Slow press", noise=0., fig=None):
    style()
    if fig is None:
        fig = plt.figure(figsize=(13, 4.5), layout="constrained")
    else:
        fig.clear()
    axes = fig.subplots(1, 2)
    for name in METHODS:
        tr = predictions[name]
        x = tr.time-tr.time[0]
        label = name+ (" (privileged)" if name == "True state" else "")
        kw = dict(color=COLORS[name], lw=2.2, ls="--" if name == "True state" else "-", label=label)
        axes[0].plot(x, tr.force, **kw)
        axes[1].plot(x, tr.markers.mean(axis=1)*1e6, **kw)
    for ax in axes:
        ax.axvline(0, color="#7B8A99", ls=":")
        ax.set_xlabel("Time after prediction cut (s)")
    axes[0].set(ylabel="Contact force (N)", title="Command-driven spatial rollouts")
    axes[1].set(ylabel="Mean outward lateral motion (um)", title="Solved lateral deformation")
    axes[0].legend(loc="upper left")
    fig.suptitle(f"Future response: {action} | noise x{noise:g}", fontsize=14)
    return fig


def sweep_figure(result, fig=None):
    style()
    rows = result["rows"]
    if fig is None:
        fig = plt.figure(figsize=(12, 4.5), layout="constrained")
    else:
        fig.clear()
    axes = fig.subplots(1, 2)
    x = [r["window_seconds"] for r in rows]
    for ax, key, scale, label in ((axes[0], "force_rmse_N", 1e3, "Force RMSE (mN)"),
                                  (axes[1], "marker_rmse_m", 1e6, "Lateral RMSE (um)")):
        y = [r[key]*scale for r in rows]
        ax.plot(x[:-1], y[:-1], "o-", color=COLORS["Short classical"], lw=2, label="Finite-window fit")
        ax.scatter(x[-1], y[-1], marker="*", s=150, color=COLORS["Full classical"], label="Full replay; known relaxed start", zorder=4)
        ax.set(xlabel="Observed history duration (s); 0 = snapshot", ylabel=label, ylim=(0, max(y)*1.15+1e-4))
        short_window = result.get("observer_config", {}).get("short_window_seconds", .2)
        ax.axvline(short_window, color="#7B8A99", ls=":", lw=1)
        ax.legend(fontsize=9)
    fig.suptitle(f"History length | {result['excitation']} excitation | noise x{result['noise_multiplier']:g}")
    return fig


def archived_history_figure():
    style()
    source = ROOT.parent/"1D/experiments/history_dependence/runs/round2_v1/data/test_wait.npz"
    with np.load(source) as data:
        obs = data["full_observed"][0]
        cmd = data["full_commands"][0]
    dt = read_json(source.parents[1]/"config.json")["dt"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.4), layout="constrained")
    for j, color in enumerate(PAIR_COLORS):
        t = np.arange(obs.shape[1])*dt
        axes[0].plot(t, cmd[j]*1e3, color=color, label=f"Archived history {'AB'[j]}")
        axes[1].plot(t, obs[j, :, 2], color=color)
    axes[0].set(xlabel="Time (s)", ylabel="Command (mm)")
    axes[1].set(xlabel="Time (s)", ylabel="Force (N)")
    axes[0].legend()
    fig.suptitle("History dependence | archived 1D comparison", color="#7F375A", fontsize=13)
    return fig, source


def noise_excitation_figure(run):
    style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    for ax, excitation in zip(axes, ("hold", "pulse")):
        for noise, color in ((0., "#167A70"), (1., "#C04A32")):
            result, _ = sweep_for(run, excitation, noise)
            rows = result["rows"]
            ax.plot([r["window_seconds"] for r in rows[:-1]], [r["force_rmse_N"]*1e3 for r in rows[:-1]],
                    "o-", color=color, label=f"Noise x{noise:g}", lw=2)
            ax.scatter(rows[-1]["window_seconds"], rows[-1]["force_rmse_N"]*1e3, marker="*", color=color, s=130)
        ax.set(xlabel="History window (s); 0 = snapshot", ylabel="Force RMSE (mN)", title=f"{excitation.capitalize()} loading")
        ax.set_ylim(bottom=0)
        ax.legend()
    fig.suptitle("Short-window error under sensor noise | stars = full replay")
    return fig


def export_figure(fig, stem, run, sources):
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(stem.with_suffix("."+ext), bbox_inches="tight", dpi=300)
    run = Path(run)
    write_json(stem.with_suffix(".json"), {"run": str(run.resolve()), "sources": sources,
               "config": str(run/("config.json" if (run/"config.json").exists() else "study.json")),
               "manifest": str(run/("manifest.json" if (run/"manifest.json").exists() else "environment.json")),
               "source_sha256": source_hashes(), "deformation_scale": 1})


def export_all(run, animation=True):
    run = Path(run)
    started = time.perf_counter()
    out = run/"figures"
    tr = Trace.load(run/"main.npz")
    replay = ReplayFigure(tr)
    replay.update(int(np.argmax(tr.force)))
    export_figure(replay.fig, out/"01_spatial_process", run, ["main.npz"])
    if animation:
        frames = np.unique(np.r_[np.arange(0, len(tr.time), 3), len(tr.time)-1])
        ani = FuncAnimation(replay.fig, replay.update, frames=frames, interval=60, blit=False)
        ani.save(out/"01_spatial_process.gif", writer=PillowWriter(fps=17), dpi=80)
        write_json(out/"01_spatial_process_animation.json", {"source": "main.npz", "frames": len(frames), "fps": 17,
                   "display_time_scale": "Approximately half physical speed", "run": str(run), "source_sha256": source_hashes()})
    plt.close(replay.fig)
    fig = paired_figure(run)
    export_figure(fig, out/"02_matched_histories", run, ["matching.json", "histories/", "pair_refinement/"])
    plt.close(fig)
    forecasts, metrics, _ = forecasts_for(run)
    fig = forecast_figure(forecasts, metrics)
    export_figure(fig, out/"03_future_predictions", run, ["forecasts/", "matching.json"])
    plt.close(fig)
    result, _ = sweep_for(run)
    fig = sweep_figure(result)
    export_figure(fig, out/"04_history_length", run, ["sweeps/hold_noise0.json"])
    plt.close(fig)
    fig, source = archived_history_figure()
    export_figure(fig, out/"archived_history_dependence", run, [str(source)])
    plt.close(fig)
    if all((run/"sweeps"/f"{excitation}_noise{noise}.json").exists() for excitation in ("hold", "pulse") for noise in (0, 1)):
        fig = noise_excitation_figure(run)
        export_figure(fig, out/"05_noise_and_excitation", run, ["sweeps/hold_noise0.json", "sweeps/hold_noise1.json",
                       "sweeps/pulse_noise0.json", "sweeps/pulse_noise1.json"])
        plt.close(fig)
    timing = {"wall_seconds": time.perf_counter()-started, "animation": animation, "formats": ["png", "svg", "pdf"]}
    if (out/"export_timing.json").exists():
        previous = read_json(out/"export_timing.json")
        history = read_json(out/"export_timing_history.json") if (out/"export_timing_history.json").exists() else []
        write_json(out/"export_timing_history.json", history+[previous])
    write_json(out/"export_timing.json", timing)
    return timing


SENSOR_COLORS = {False: '#B45F35', True: '#2878B5'}


def information_forecast_figure(run, parent='test_5000', repeat=0, window=.8,
                                action='Slow press', channels='Both', folder=None, fig=None):
    """Four information conditions on a preselected history and noise draw."""
    from .information import method_key
    style()
    run = Path(run)
    folder = Path(folder) if folder is not None else run/'test'/parent/f'repeat_{repeat}'
    result = read_json(folder/'result.json')
    action_index = result['actions'].index(action)
    with np.load(folder/'curves.npz') as data:
        curves = dict(data)
    if fig is None:
        fig = plt.figure(figsize=(14, 5.3), layout='constrained')
    else:
        fig.clear()
    axes = fig.subplots(1, 3)
    suffix = f'_{action_index}_'
    t = curves['truth'+suffix+'time']
    x = t-t[0]
    truth = curves['truth'+suffix+'force']
    for side in (False, True):
        if channels == 'Without lateral' and side or channels == 'With lateral' and not side:
            continue
        for duration in dict.fromkeys([0., window]):
            key = method_key(side, duration)
            title = 'Snapshot' if duration == 0. else ('Contact update + propagation' if duration == 'contact' else f'{duration:g} s history')
            label = title + (' + lateral' if side else '; no lateral')
            kw = dict(color=SENSOR_COLORS[side], ls='--' if duration == 0. else '-', lw=2., label=label)
            force = curves[key+suffix+'force']
            axes[0].plot(x, force, **kw)
            axes[1].plot(x, (force-truth)*1e3, **kw)
            axes[2].plot(x, curves[key+suffix+'markers'].mean(axis=1)*1e6, **kw)
    for key, color, ls, label in [('replay', '#21836D', '-.', 'Motion replay; known relaxed start'),
                                 ('truth', '#202C3B', ':', 'True internal state (reference)')]:
        kw = dict(color=color, ls=ls, lw=1.8, label=label)
        force = curves[key+suffix+'force']
        axes[0].plot(x, force, **kw)
        axes[1].plot(x, (force-truth)*1e3, **kw)
        axes[2].plot(x, curves[key+suffix+'markers'].mean(axis=1)*1e6, **kw)
    for ax in axes:
        ax.axvline(0, color='#8B939C', ls=':', lw=1)
        ax.set_xlabel('Time after prediction cut (s)')
    axes[0].set(ylabel='Contact force (N)', title='Future response', ylim=(0, None))
    axes[1].set(ylabel='Predicted minus true force (mN)', title='Prediction difference')
    axes[2].set(ylabel='Mean outward motion (um)', title='Lateral deformation')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='outside lower center', ncol=2, fontsize=10, frameon=False)
    fig.suptitle(f'{parent} | noise repeat {repeat} | {action} | cut at {t[0]:.2f} s', fontsize=14)
    return fig


def information_window_figure(run, action='Slow press'):
    """Aggregate errors plus explicitly separated phase/contact/update intervals."""
    from .information import method_key
    style()
    run = Path(run)
    spec = read_json(run/'study.json')
    jobs = [read_json(p) for p in sorted((run/'test').glob('*/repeat_*/result.json'))]
    parent = f"test_{spec['test_seeds'][0]}"
    first = next(j for j in jobs if j['parent_id']==parent and j['repeat']==0)
    trace = Trace.load(run/'histories'/f'{parent}.npz')
    with np.load(run/'test'/parent/'repeat_0/curves.npz') as data:
        observed = data['observed']
    fig = plt.figure(figsize=(13, 9.2), layout='constrained')
    grid = fig.add_gridspec(2, 2, height_ratios=(1, 1.1))
    axes = [fig.add_subplot(grid[0, i]) for i in range(2)]
    timeline = fig.add_subplot(grid[1, :])
    rng = np.random.default_rng(spec['noise_root_seed'])

    def parent_values(method):
        return np.array([np.mean([r['force_rmse_N']*1e3 for j in jobs if j['parent_id']==f'test_{seed}'
                                 for r in j['rows'] if r['method']==method and r['action']==action])
                         for seed in spec['test_seeds']])

    for side in (False, True):
        color = SENSOR_COLORS[side]
        label = 'With lateral' if side else 'Without lateral'
        for ax, keys, x in [(axes[0], [method_key(side,w) for w in spec['windows_seconds']], spec['windows_seconds']),
                           (axes[1], [method_key(side,.2),method_key(side,'contact')], [0,1])]:
            values = np.array([parent_values(key) for key in keys])
            means = values.mean(axis=1)
            intervals = np.array([np.quantile(rng.choice(v,(2000,len(v))).mean(axis=1), [.025,.975]) for v in values])
            ax.errorbar(x, means, yerr=np.maximum(0,np.array([means-intervals[:,0],intervals[:,1]-means])),
                        color=color, marker='o', lw=2, capsize=4, label=label)
            ax.set(ylabel='Force RMSE (mN)', ylim=(0,None))
            ax.legend(frameon=False)
    axes[0].set(xticks=spec['windows_seconds'], xlabel='Recent window (s); 0 = snapshot', title='Duration changes the available data')
    axes[1].set(xticks=[0,1], xticklabels=['Recent wait\n0.2 s update','Earlier contact\n0.2 s update + propagation'],
                title='Same update duration, different data')
    # Command phases are distinct from contact detected in the noisy force.
    phase_bands(timeline, trace, labels=True)
    detected = observed[:,2] > spec['contact_threshold_N']
    dt = trace.config['dt']
    timeline.broken_barh([(trace.time[i-1],dt) for i in range(1,len(detected)) if detected[i]],
                         (4.65,.35), facecolors='#26344A')
    timeline.text(trace.time[0]+.01, 5.1, f'Contact: measured force > {spec["contact_threshold_N"]*1e3:g} mN', fontsize=10)
    for y, duration in enumerate([.8,.2,0.,'contact']):
        row = next(r for r in first['rows'] if r['method']==method_key(False,duration) and r['action']==action)
        info = row['inference']
        begin,end = info['update_interval_s']
        stop = info['propagation_interval_s'][1]
        if end>begin:
            timeline.plot([begin,end],[y,y],color='#2878B5',lw=9,solid_capstyle='butt')
        else:
            timeline.scatter([end],[y],color='#2878B5',s=55,zorder=5)
        if stop>end:
            timeline.plot([end,stop],[y,y],color='#9CA3AA',ls='--',lw=3)
            timeline.text((end+stop)/2,y+.15,f'Motion only: {stop-end:.2f} s',ha='center',fontsize=10)
        if duration != 0.:
            timeline.text(begin-.02,y,f'{info["observed_contact_seconds"]:.2f} s contact',ha='right',va='center',fontsize=10)
    timeline.axvline(trace.time[-1],c='#A94A4A',ls=':',lw=1.5)
    timeline.plot([],[],lw=8,color='#2878B5',label='Force / shape update')
    timeline.plot([],[],ls='--',lw=3,color='#9CA3AA',label='Measured-position propagation')
    timeline.set(xlim=(trace.time[0],trace.time[-1]+.04),ylim=(-.5,5.45),
                 yticks=[0,1,2,3],yticklabels=['Recent 0.8 s','Recent 0.2 s','Snapshot','Earlier contact'],
                 xlabel=f'Time (s) | first prespecified history: {parent}, repeat 0')
    timeline.legend(loc='upper left',bbox_to_anchor=(0,-.18),ncol=2,frameon=False)
    fig.suptitle(f'{action} | {len(spec["test_seeds"])} histories; three noise repeats averaged within each\n'
                 'Bars: pointwise 95% bootstrap intervals over histories', fontsize=14)
    fig.supxlabel('Contact selection scans all prior force; motion is used from update start to prediction cut.',fontsize=10)
    return fig


def information_gain_figure(run):
    style()
    import textwrap
    from .information import CONTRASTS
    summary = read_json(Path(run)/'summary.json')
    fig, ax = plt.subplots(figsize=(13,8.3), layout='constrained')
    labels = list(CONTRASTS)
    for offset,action,color in [(-.15,'Slow press','#2878B5'),(.15,'Fast press','#7C4C9B')]:
        for i,label in enumerate(labels):
            row = next(r for r in summary['contrasts'] if r['contrast']==label and r['action']==action)
            vals = np.array([r['improvement_mN'] for r in row['parent_values']])
            y = i+offset
            ax.scatter(vals, y+np.linspace(-.06,.06,len(vals)),s=18,color=color,alpha=.25,zorder=2)
            mean,ci = row['mean_improvement_mN'],row['ci95_mN']
            ax.errorbar(mean,y,xerr=[[max(0,mean-ci[0])],[max(0,ci[1]-mean)]],
                        color=color,marker='o',ms=7,lw=2,capsize=4,zorder=3,
                        label=action if i==0 else None)
    ax.axvline(0,color='#555E68',lw=1,ls='--')
    ax.set(yticks=range(len(labels)),yticklabels=['\n'.join(textwrap.wrap(s,36)) for s in labels],
           xlabel='Paired force-error reduction (mN) | positive = improvement')
    ax.invert_yaxis()
    ax.legend(frameon=False,loc='lower right')
    fig.suptitle('What changes prediction?\nEach faint point is one history, averaged over three noise repeats',fontsize=15)
    fig.supxlabel('Solid points and bars: mean and pointwise 95% bootstrap interval. Fast press reuses the same estimated state.',fontsize=10)
    return fig


def export_information(run):
    run = Path(run)
    sources = ['study.json','physics.json','calibration.json','summary.json','metrics.csv','histories/','test/']
    for name, figure in [('01_information_curves',information_forecast_figure(run)),
                         ('02_window_and_contact',information_window_figure(run)),
                         ('03_paired_improvements',information_gain_figure(run))]:
        export_figure(figure,run/'figures'/name,run,sources)
        plt.close(figure)

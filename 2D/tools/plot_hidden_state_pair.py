"""Recorded spatial contact, matched observations and a common future action."""
from pathlib import Path
import csv
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle
import numpy as np

from nr2d.physics import Config, SpatialModel, Trace

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'runs/2d_contact/pilot_c9dd23016896'
OUT = ROOT / 'docs/figures'
OUT.mkdir(parents=True, exist_ok=True)
matching = json.loads((RUN / 'matching.json').read_text())
parents = [matching['selected'][key] for key in ('a', 'b')]
history_paths = [RUN / 'histories' / f'{parent}.npz' for parent in parents]
future_paths = [RUN / 'pair_refinement' / f'default_{parent}.npz' for parent in parents]
histories = [Trace.load(path) for path in history_paths]
futures = [Trace.load(path) for path in future_paths]
assert np.array_equal(futures[0].command, futures[1].command), 'Interventions differ'
assert np.array_equal(futures[0].time, futures[1].time), 'Future clocks differ'
residual = np.abs(histories[0].observation[-1] - histories[1].observation[-1])
np.testing.assert_allclose(residual, matching['selected']['residual_SI'], rtol=0, atol=1e-15)
assert np.all(residual <= matching['resolution_SI'])

plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['DejaVu Sans'],
    'font.size': 11, 'axes.titlesize': 12,
    'axes.labelsize': 11, 'xtick.labelsize': 10, 'ytick.labelsize': 10,
    'legend.fontsize': 10, 'legend.frameon': False,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.linewidth': .7, 'svg.fonttype': 'none', 'pdf.fonttype': 42,
})
fig = plt.figure(figsize=(12.6, 7.6), facecolor='white')
grid = fig.add_gridspec(2, 3, width_ratios=(1, 1.35, 1.65), height_ratios=(1, 1.05),
                        left=.055, right=.985, top=.92, bottom=.09, wspace=.48, hspace=.62)
body_ax = fig.add_subplot(grid[0, 0])
history_ax = fig.add_subplot(grid[0, 1])
current_ax = fig.add_subplot(grid[0, 2])
force_ax = fig.add_subplot(grid[1, :2])
lateral_ax = fig.add_subplot(grid[1, 2])
colors = ['#275D9B', '#AE4774']
styles = ['-', '--']


def title(axis, letter, label):
    axis.set_title(label, loc='left', pad=14)
    axis.annotate(letter, xy=(0, 1), xycoords='axes fraction', xytext=(-27, 15),
                  textcoords='offset points', fontsize=13, weight='bold')


# The body snapshot illustrates the setup; it does not select either history.
history = histories[0]
model = SpatialModel(Config(**history.config))
frame = int(np.argmax(history.force))
nodes = model.nodes + history.u[frame].reshape(-1, 2)
mesh = PolyCollection(nodes[model.tri] * 1e3, facecolors='#e9eef3',
                      edgecolors='#aab7c4', linewidths=.28)
body_ax.add_collection(mesh)
body_ax.add_patch(Circle((0, (model.c.height + model.c.radius - history.d[frame]) * 1e3),
                        model.c.radius * 1e3, facecolor='#c4cbd2', edgecolor='#667687', lw=.9))
body_ax.plot([-model.c.width * 500, model.c.width * 500], [0, 0], color='#3b4651', lw=2)
body_ax.scatter(*nodes[model.marker_nodes].T * 1e3, color='#187d78', edgecolors='white',
                 linewidths=.6, s=24, zorder=5)
body_ax.set(xlim=(-23, 23), ylim=(-1, 25), xlabel='x (mm)', ylabel='y (mm)', aspect='equal')
body_ax.set_xticks([-20, 0, 20])
body_ax.set_yticks([0, 10, 20])
title(body_ax, 'a', '2D body and indenter')
body_ax.text(.5, -.46, 'History A at peak load\nDeformation scale 1:1', transform=body_ax.transAxes,
             ha='center', va='top', fontsize=10, color='#62676d')

for trace, letter, color, linestyle in zip(histories, ('A', 'B'), colors, styles):
    history_ax.plot(trace.time - trace.time[-1], trace.d * 1e3, color=color,
                    ls=linestyle, lw=1.9, label=f'History {letter}')
history_ax.axvline(0, color='#7c8188', ls=':', lw=.9)
history_ax.set(xlim=(-1.4, .04), ylim=(-.18, .42), xlabel='Time before prediction (s)',
               ylabel='Actual tool position (mm)')
history_ax.set_xticks([-1.4, -.7, 0])
history_ax.legend(loc='upper right', fontsize=10)
title(history_ax, 'b', 'Loading histories')

current_ax.set_axis_off()
title(current_ax, 'c', 'At the prediction time')
factors = np.array([1e3, 1e3, 1e3, 1e6, 1e6])
labels = ['Position (mm)', 'Velocity (mm/s)', 'Force (mN)', 'Left side (µm)', 'Right side (µm)']
observed = np.array([trace.observation[-1] for trace in histories]) * factors
limits = np.array(matching['resolution_SI']) * factors
rows = []
for i, label in enumerate(labels):
    precision = 3 if i < 3 else 2
    rows.append([label, f'{observed[0,i]:.{precision}f}', f'{observed[1,i]:.{precision}f}',
                 f'{residual[i]*factors[i]:.3g}', f'{limits[i]:.3g}'])
table = current_ax.table(cellText=rows, colLabels=['Channel', 'A', 'B', '|A-B|', 'Limit'],
                         colWidths=[.40, .15, .15, .15, .15], cellLoc='right',
                         loc='upper left', bbox=[-.04, .21, 1.08, .77])
table.auto_set_font_size(False)
table.set_fontsize(10)
for (row, column), cell in table.get_celld().items():
    cell.set_edgecolor('#e0e3e6')
    cell.set_linewidth(.4)
    cell.set_facecolor('#f3f5f7' if row == 0 else 'white')
    if column == 0:
        cell.set_text_props(ha='left')
    if row == 0:
        cell.set_text_props(weight='bold')
current_ax.text(-.02, .09, 'All five channels within synthetic tolerances.\nLateral readings are close, not identical.',
                transform=current_ax.transAxes, fontsize=10, va='top', linespacing=1.5, color='#62676d')

for trace, letter, color, linestyle in zip(futures, ('A', 'B'), colors, styles):
    time = trace.time - trace.time[0]
    force_ax.plot(time, trace.force * 1e3, color=color, ls=linestyle, lw=1.9, label=f'History {letter}')
    lateral_ax.plot(time, np.mean(trace.markers, axis=1) * 1e6, color=color, ls=linestyle, lw=1.9)
for axis in (force_ax, lateral_ax):
    axis.axvline(0, color='#7c8188', ls=':', lw=.9)
    axis.set_xlim(0, 1)
    axis.set_xlabel('Time after prediction (s)')
    axis.set_ylim(bottom=0)
    axis.grid(axis='y', color='#e3e6e9', lw=.5)
force_ax.set_ylabel('Contact force (mN)')
force_ax.legend(loc='upper left')
force_ax.text(.98, .08, 'Slow press: 0.4 mm target, 0.65 s ramp', transform=force_ax.transAxes,
               ha='right', va='bottom', fontsize=10, color='#62676d')
lateral_ax.set_ylabel('Mean lateral displacement (µm)')
title(force_ax, 'd', 'Response to the same command')
title(lateral_ax, 'e', 'Lateral response')

fig.savefig(OUT / 'hidden_state_pair.svg', facecolor='white', metadata={'Creator': 'NR material state'})
fig.savefig(OUT / 'hidden_state_pair.pdf', facecolor='white', metadata={'Creator': 'NR material state'})
fig.savefig(OUT / 'hidden_state_pair.png', dpi=300, facecolor='white', metadata={'Creator': 'NR material state'})
plt.close(fig)

with (OUT / 'hidden_state_pair.csv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.writer(stream)
    writer.writerow(['phase', 'parent', 'time_from_prediction_s', 'command_m',
                     'position_m', 'velocity_m_s', 'force_N', 'left_m', 'right_m'])
    for phase, traces in [('history', histories), ('future', futures)]:
        for parent, trace in zip(parents, traces):
            origin = trace.time[-1] if phase == 'history' else trace.time[0]
            writer.writerows([phase, parent, t-origin, command, position, velocity, force, left, right]
                             for t, command, position, velocity, force, (left, right)
                             in zip(trace.time, trace.command, trace.d, trace.v, trace.force, trace.markers))
source_files = history_paths + future_paths + [RUN / 'matching.json', Path(__file__).resolve(),
                                                ROOT / 'src/nr2d/physics.py']
provenance = {
    'claim': 'The preselected histories have similar current readings and different subsequent simulated responses.',
    'scope': 'One preselected pair from an eight-history synthetic pilot; lateral residuals remain.',
    'archetype': 'asymmetric mixed-modality figure', 'backend': 'Python / Matplotlib',
    'size_inches': [12.6, 7.6], 'raster_dpi': 300, 'editable_text': ['SVG', 'PDF'],
    'run': RUN.relative_to(ROOT).as_posix(), 'parents': parents, 'action': 'Slow press',
    'pair_selection': matching['selection_rule'], 'future_used_for_selection': False,
    'commands_identical': True, 'observation_residual_SI': residual.tolist(),
    'matching_limits_SI': matching['resolution_SI'],
    'max_force_difference_mN': float(np.max(np.abs(futures[0].force - futures[1].force))*1e3),
    'rms_force_difference_mN': float(np.sqrt(np.mean((futures[0].force - futures[1].force)**2))*1e3),
    'body_frame': {'parent': parents[0], 'index': frame, 'rule': 'peak force within the fixed first history',
                   'deformation_scale': 1},
    'transforms': {'time': 'relative to prediction cut', 'lateral_response': 'mean of left and right markers',
                   'force_display': 'N to mN', 'position_display': 'm to mm', 'lateral_display': 'm to um'},
    'counts': {'history_frames': [len(t.time) for t in histories], 'future_frames': [len(t.time) for t in futures]},
    'exclusions': 'None within the requested pair; all five endpoint channels are shown.',
    'export_scope': 'README and presentation figure; 300 dpi PNG and vector exports, not a journal submission package.',
    'statistics': 'Descriptive traces; two histories, no confidence interval or population test.',
    'source_sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
}
(OUT / 'hidden_state_pair.json').write_text(json.dumps(provenance, indent=2)+'\n', encoding='utf-8')
print(OUT / 'hidden_state_pair.png')

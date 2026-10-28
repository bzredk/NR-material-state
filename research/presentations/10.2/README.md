# 10.2

[All reports](../README.md) · [2D experiment](../../../2D/README.md)

[PowerPoint](output/10.2.pptx) · [PDF](output/10.2.pdf) · [Chinese speaking notes](output/speaker-notes.zh-CN.md)

Twelve main slides for a 10–12 minute report, followed by three appendix slides and a final discussion page. The English slides follow the white background, Arial typography and restrained layout of `10_1.pdf`. Chinese speaking notes are also embedded in the PowerPoint.

The report connects the earlier 1D results to spatial 2D contact, compares current lateral sensing with interaction history, then separates recent waiting from earlier contact observations. The final page asks about research focus, real-robot experiments and how the fast/slow force example connects back to the broader research idea, based on the user-provided voice memo and clarification.

## Evidence

The experiment overview and [related papers](../../../2D/README.md#related-reading) live in the 2D guide.

- Main results: [`channels_contact_20261026`](../../../2D/runs/information/channels_contact_20261026/RESULTS.md), with 24 independent loading histories and three noise draws per history.
- Physical-process figure: the recorded [`2D pilot`](../../../2D/runs/2d_contact/pilot_c9dd23016896/RESULTS.md), explicitly identified as a separate run.
- Earlier results: [`1D/RESULTS.md`](../../../1D/RESULTS.md).
- Visual reference: [`10_1.pdf` on Drive](https://drive.google.com/file/d/1G0rtBQNcx_zp9Ejve4MJSitq-1gqHxlA/view). Its local source hash is recorded in `assets/slide_data.json`.
- Per-slide sources and Chinese notes: [`slide_sources.json`](slide_sources.json).

The deck reports recorded experiments. Creating it did not rerun the simulations. Recursive estimation, uncertainty calibration, common-feedback action tests, 3D robot simulation and hardware remain planned work.

## Editing and rebuilding

The nine charts and eight tables are native PowerPoint objects. Their embedded workbooks contain value snapshots, not live links to the experiment. The FEM process figure remains an image.

Open the PPTX in PowerPoint to edit directly. To rebuild in the existing Codex authoring environment, run from this folder:

```powershell
python prepare_data.py
$env:DECK_REVISION = '_rebuilt'
node build.mjs
```

`prepare_data.py` needs NumPy. `build.mjs` uses the bundled `@oai/artifact-tool` runtime and presentation validators, whose local paths are declared at the top of the file. A fresh suffix avoids overwriting the delivered deck. Use PowerPoint's PDF export for the final preview. Build intermediates stay in ignored directories.

`output/` contains the report and speaking notes. `assets/` contains source data and provenance. Local build files, validation records and automatic transcripts are excluded from Git.

# 10.2

[PowerPoint](output/10.2.pptx) · [PDF](output/10.2.pdf) · [Chinese speaking notes](output/speaker-notes.zh-CN.md)

Twelve main slides for a 10–12 minute report, followed by three appendix slides and a final discussion page. The English slides follow the white background, Arial typography and restrained layout of `10_1.pdf`. Chinese speaking notes are also embedded in the PowerPoint.

The report connects the earlier 1D results to spatial 2D contact, compares current lateral sensing with interaction history, then separates recent waiting from earlier contact observations. The final page asks about research focus, real-robot experiments and how the fast/slow force example connects back to the broader research idea, based on the user-provided voice memo and clarification.

## Evidence

- Main results: [`channels_contact_20261026`](../../../2D/runs/information/channels_contact_20261026/RESULTS.md), with 24 independent loading histories and three noise draws per history.
- Physical-process figure: the recorded [`2D pilot`](../../../2D/runs/2d_contact/pilot_c9dd23016896/RESULTS.md), explicitly identified as a separate run.
- Earlier results: [`1D/RESULTS.md`](../../../1D/RESULTS.md).
- Visual reference: [`10_1.pdf` on Drive](https://drive.google.com/file/d/1G0rtBQNcx_zp9Ejve4MJSitq-1gqHxlA/view). Its local source hash is recorded in `assets/slide_data.json`.
- Per-slide sources and Chinese notes: [`slide_sources.json`](slide_sources.json).

The deck reports recorded experiments. Creating it did not rerun the simulations. Recursive estimation, uncertainty calibration, common-feedback action tests, 3D robot simulation and hardware remain planned work.

## Related reading

Six references for the report's questions about state, robot experiments and the broader idea behind the fast/slow force example. Paper IDs match the existing research notes.

| Reference | Connection to this experiment |
| --- | --- |
| **T03 — Predictive Representations of State.** Littman, Sutton and Singh, NIPS 2001. [Paper](https://proceedings.neurips.cc/paper/2001/file/1e4d36177d71bbb3558e43af9577d70e-Paper.pdf). | Defines state through predictions of future action–observation tests. This motivates evaluating a representation by the future interactions it predicts, without requiring recovery of unique physical coordinates. The paper's discrete formulation does not establish sufficiency of our finite observation windows. |
| **P01 — RoboPack: Learning Tactile-Informed Dynamics Models for Dense Packing.** Ai et al., RSS 2024. [Paper](https://www.roboticsproceedings.org/rss20/p130.html). | Infers object geometry and latent physical information from vision and touch, then predicts dynamics for MPC. A close precedent for the estimation–prediction–control chain, with richer tactile and point-cloud observations than our force and lateral-shape channels. |
| **P16 — HIRE: History-Conditioned Interaction Reasoning and High-Rate Execution for Visually Aliased Precision Manipulation.** Li et al., arXiv preprint, v1, 2026. [Paper](https://arxiv.org/abs/2609.30828v1). | Uses ordered wrench history and contact feedback to resolve ambiguous interaction progress on real robots. Directly relevant to the claim that history can change the appropriate action; its task/contact representation differs from the internal relaxation variables examined here. |
| **P03 — Rapid Mismatch Estimation via Neural Network Informed Variational Inference.** Jaszczuk and Figueroa, CoRL 2025. [Paper](https://proceedings.mlr.press/v305/jaszczuk25a.html). | Combines a learned prior with variational inference to estimate payload mass and center of mass from proprioception, including uncertainty. A useful reference for short-window estimation and robot integration. These are unknown payload parameters, distinct from evolving internal material state. |
| **P02 — AdaptiGraph: Material-Adaptive Graph-Based Neural Dynamics for Robotic Manipulation.** Zhang et al., RSS 2024. [Paper](https://arxiv.org/abs/2407.07889). | Adapts material properties from interactions for particle-graph prediction and MPC. It also uses recent particle positions, so it is not a memoryless baseline. It helps separate unknown-property adaptation from our experiment, which holds material parameters fixed while histories change internal state. |
| **P04 — Viscoelasticty with physics-augmented neural networks: model formulation and training methods without prescribed internal variables.** Rosenkranz et al., Computational Mechanics 74, 1279–1301, 2024. [Published paper](https://doi.org/10.1007/s00466-024-02477-1) · [Full text](https://arxiv.org/html/2401.14270v1). | Learns constitutive evolution from strain/stress paths without supplied internal-variable trajectories. This is a direct precedent for material memory and its evolution. Our inference problem uses sparse boundary force and lateral shape, rather than material-point strain/stress measurements. |

History encoding and material internal variables are established ideas. Our current experiment isolates what lateral sensing and contact/recovery history add to prediction with the physical model and future actions held fixed. Whether this improves robot decisions remains open.

The [method audit](../../hidden_state_reframing/closest_work.md) records observations, supervision, hardware, code and reproduction limits for P01–P04 and P16. The [state formulation](../../hidden_state_reframing/formalization.md) covers the theory and connects it to the current model. These are literature comparisons, not reproduced external baselines.

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

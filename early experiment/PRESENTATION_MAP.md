# Progress slides: source map

The [PowerPoint](presentation/NR_Progress_2026-10-22.pptx) and [PDF](presentation/NR_Progress_2026-10-22.pdf) contain the 12-slide presentation saved October 22, 2026. Both retain the original file contents.

| Slide | Subject | Evidence / implementation |
| --- | --- | --- |
| 1 | Thesis roadmap | Research framing; no new experimental claim |
| 2 | Policy reuse | Intended interface: history, state, candidate-policy response |
| 3 | Repeated contact | E1 matched histories, E2 transfer, E3 action-value test |
| 4 | Water-rich gel | Literature motivation and conceptual illustration; not a measured project sample |
| 5 | RME, CPF and NR | Related estimation targets; neither paper method is integrated in the completed runs |
| 6 | History-based inference | Related work and design motivation |
| 7 | Hidden material memory | Two Maxwell state components can share current force and evolve differently |
| 8 | Training process | E1/E2 history encoder, fixed physical rollout, future-response loss |
| 9 | Equations | E1 `models.py`, `differentiable.py`; E2 `models.py`, `dynamics.py`, `physics_base.py` |
| 10 | Baseline characteristics | Implemented classical references plus explicitly planned paper adaptations |
| 11 | Three current findings | E1 history ambiguity; E2 future-control transfer; E3 negligible added benefit under shared feedback |
| 12 | References | E1/E2/E3 sources and P1 collection plan |

The E2 result is in [`experiments/02_transfer/v2/runs/transfer_v2`](experiments/02_transfer/v2/runs/transfer_v2). The parent `transfer_v1` records an earlier experiment with a different controller-switch interpretation.

The original workflow diagram uses 301 observations, five channels and a 32-unit GRU. It depicts the controlled-transfer implementation, not the earlier pilot's 151-observation sequence. Its "two material states" label refers to latent/internal state dimension, not planar motion or a two-dimensional mesh.

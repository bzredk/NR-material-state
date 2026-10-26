# Executed spatial 2D pilot

Run: `pilot_c9dd23016896`. Synthetic material; eight independent test parents.

| Future | Noise | Method | Mean force RMSE (mN) | Parent range (mN) |
|---|---:|---|---:|---:|
| Slow press | 0 | Snapshot | 1.3187 | 0.5462–1.8675 |
| Slow press | 0 | Short classical | 1.1010 | 0.8326–1.2528 |
| Slow press | 0 | Full classical | 0.0000 | 0.0000–0.0000 |
| Slow press | 1 | Snapshot | 1.6596 | 0.9968–2.1657 |
| Slow press | 1 | Short classical | 2.3766 | 2.1393–2.5034 |
| Slow press | 1 | Full classical | 0.0075 | 0.0066–0.0091 |
| Fast press | 0 | Snapshot | 1.5747 | 0.6001–2.1408 |
| Fast press | 0 | Short classical | 0.9226 | 0.7230–1.0334 |
| Fast press | 0 | Full classical | 0.0000 | 0.0000–0.0000 |
| Fast press | 1 | Snapshot | 1.9662 | 1.2429–2.4657 |
| Fast press | 1 | Short classical | 2.3322 | 2.1777–2.4155 |
| Fast press | 1 | Full classical | 0.0086 | 0.0075–0.0103 |

These are descriptive means of per-parent RMSE, not independent frame statistics.
The 0.2 s observer helps without noise, but loses to snapshot under nominal noise. Full replay benefits from known parameters and a known relaxed start.
No controller was compared in this spatial pilot. No learned-state novelty or long-history necessity follows from these numbers.

Numerical pilot computation: 72.34 s. Batch execution: 175.21 s.
The batch timer includes cache replay for already computed conditions; it is not a clean all-cold benchmark.

Main physical checks passed 17/17. Whole-history audit additionally identified the following retained over-limit case:
- `histories\validation_200.npz`: penetration 5.0247 um exceeds 5 um. Diagnostic doubled penalty: 2.6450 um; force NRMSE change 0.5425%. The original is retained and the diagnostic is excluded from the test comparison.

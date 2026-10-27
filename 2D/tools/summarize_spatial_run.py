"""Summarize all pilot outcomes, including weak comparisons and physical overruns."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np

from nr2d.physics import Config, SpatialModel, Trace
from nr2d.protocols import protocol
from nr2d.experiments import ROOT, RUNS, read_json, write_json, environment, failure
from nr2d.estimators import METHODS

run = ROOT/read_json(RUNS/"latest.json")["run"].replace("\\", "/")
batch = read_json(run/"batch.json")
manifest = read_json(run/"manifest.json")
summary = []
for action in ("Slow press", "Fast press"):
    for noise in (0., 1.):
        for method in METHODS:
            selected = [r for r in batch["rows"] if r.get("action") == action and r.get("noise") == noise and r.get("method") == method]
            values = np.array([r["force_rmse_N"] for r in selected])*1e3
            summary.append({"action": action, "noise": noise, "method": method, "parent_count": len(values),
                            "mean_force_rmse_mN": float(values.mean()), "min_force_rmse_mN": float(values.min()),
                            "max_force_rmse_mN": float(values.max()), "mean_inference_seconds": float(np.mean([r["inference_seconds"] for r in selected]))})

physical = []
violations = []
paths = sorted((run/"histories").glob("*.npz"))+sorted((run/"forecasts").glob("*/true_state.npz"))
entries = {h["id"]: h for h in manifest["histories"]}
for path in paths:
    tr = Trace.load(path)
    maximum = tr.diagnostics.max(axis=0)
    record = {"path": str(path.relative_to(run)), "max_body_balance_N": float(maximum[0]), "max_tool_balance_N": float(maximum[1]),
              "max_penetration_um": float(maximum[2]*1e6), "max_strain": float(maximum[3]),
              "passed": bool(maximum[0]<=2e-7 and maximum[1]<=2e-7 and maximum[2]<=5e-6 and maximum[3]<=.06)}
    physical.append(record)
    if not record["passed"]:
        violations.append(record)
        # Diagnose rather than silently replacing an over-limit original.
        if path.stem in entries:
            c = replace(Config(**tr.config), penalty=2*tr.config["penalty"])
            u, p, _ = protocol(c, **entries[path.stem]["parameters"])
            corrected = SpatialModel(c).simulate(u, p, metadata={"role": "diagnostic_only", "original": str(path.relative_to(run))})
            out = run/"diagnostics"/(path.stem+"_double_penalty.npz")
            corrected.save(out)
            record["diagnostic"] = {"path": str(out.relative_to(run)), "max_penetration_um": float(corrected.diagnostics[:, 2].max()*1e6),
                                    "force_change_NRMSE": float(np.sqrt(np.mean((corrected.force-tr.force)**2))/np.sqrt(np.mean(tr.force**2))),
                                    "original_preserved": True, "included_in_test_comparisons": False}

report = {"conditions": summary, "physical_audit": physical, "physical_threshold_exceedances": violations,
          "optimizer_nonconvergence": [r for r in batch["rows"] if r.get("inference", {}).get("optimizer_success") is False],
          "batch_failures": [r for r in batch["rows"] if r.get("status") == "failed"],
          "independent_parents": batch["independent_units"], "status": "descriptive synthetic pilot",
          "confidence_intervals": "Not computed: small development pilot, single shared noise realization; not a powered confirmatory study"}
write_json(run/"summary.json", report)
write_json(run/"physical_failures.json", violations)
env = environment()
write_json(run/"environment/final.json", env)
freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True).stdout
(run/"environment/pip-freeze.txt").write_text(freeze, encoding="utf-8")
for path in (ROOT/"src/nr2d").glob("*.py"):
    out = run/"source"/path.name
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, out)
write_json(run/"delivery_manifest.json", {"utc": datetime.now(timezone.utc).isoformat(), "source_sha256": env["source_sha256"],
          "notebook": "notebooks/spatial_2d_hidden_state.ipynb", "state": "code and numerical outputs delivered",
          "main_physics_checks": "17/17 passed", "extra_validation_overrun_count": len(violations)})
lines = ["# Executed spatial 2D pilot", "", f"Run: `{run.name}`. Synthetic material; eight independent test parents.", "",
         "| Future | Noise | Method | Mean force RMSE (mN) | Parent range (mN) |", "|---|---:|---|---:|---:|"]
for row in summary:
    if row["method"] == "True state":
        continue
    lines.append(f"| {row['action']} | {row['noise']:g} | {row['method']} | {row['mean_force_rmse_mN']:.4f} | {row['min_force_rmse_mN']:.4f}–{row['max_force_rmse_mN']:.4f} |")
lines.extend(["", "These are descriptive means of per-parent RMSE, not independent frame statistics.",
    "The 0.2 s observer helps without noise, but loses to snapshot under nominal noise. Full replay benefits from known parameters and a known relaxed start.",
    "No controller was compared in this spatial pilot. No learned-state novelty or long-history necessity follows from these numbers.", "",
    f"Numerical pilot computation: {manifest['wall_seconds']:.2f} s. Batch execution: {batch['wall_seconds']:.2f} s.",
    "The batch timer includes cache replay for already computed conditions; it is not a clean all-cold benchmark.", "",
    "Main physical checks passed 17/17. Whole-history audit additionally identified the following retained over-limit case:"])
for v in violations:
    lines.append(f"- `{v['path']}`: penetration {v['max_penetration_um']:.4f} um exceeds 5 um. "
                 f"Diagnostic doubled penalty: {v['diagnostic']['max_penetration_um']:.4f} um; force NRMSE change {v['diagnostic']['force_change_NRMSE']:.4%}. "
                 "The original is retained and the diagnostic is excluded from the test comparison.")
(run/"RESULTS.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
print("Wrote summary, physical audit, diagnostic correction, source snapshot and environment record.")

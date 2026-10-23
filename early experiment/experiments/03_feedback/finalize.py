"""Package completed measurements; no inference, simulation or tuning."""
from pathlib import Path
import hashlib
import json
import platform
import importlib.metadata
import numpy as np

ROOT = Path(__file__).resolve().parent

def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    s = read("results/summary.json")
    p = dict(np.load(ROOT / "raw/prepared.npz"))
    pred = s["prediction"]["by_method"]
    seeds = read("config.json")["seeds"]
    family = {}
    for name in ["history", "snapshot"]:
        rows = [pred[f"{name}_state_{seed}"] for seed in seeds]
        family[name] = {
            "original_cut_recontact_rmse_N": float(np.mean(
                [r["original_cut_recontact_rmse_N"] for r in rows])),
            "force_rmse_at_relative_time": {
                t: float(np.mean([r["at_relative_time"][t]["force_rmse_N"] for r in rows]))
                for t in rows[0]["at_relative_time"]
            }
        }
    prefix = {}
    for name in ["history_state_11", "snapshot_state_11", "classical"]:
        z = p["prefix_z_" + name]
        err = np.sqrt(np.mean((z-p["prefix_truth"][:, :, 2:])**2, axis=(0, 2)))*1000
        prefix[name] = {"rmse_mm_at_cut": float(err[0]), "rmse_mm_at_handoff": float(err[-1])}
    h = family["history"]["original_cut_recontact_rmse_N"]
    c = family["snapshot"]["original_cut_recontact_rmse_N"]
    numbers = {
        "family_prediction": family,
        "relative_rmse_reduction_percent": (1-h/c)*100,
        "snapshot_over_history_rmse": c/h,
        "seed11_prefix_state_diagnostic": prefix,
        "prefix_peak_range_N": [float(p["prefix_peak"].min()), float(p["prefix_peak"].max())],
        "recorded_wall_seconds": {
            "prepare": read("results/interface.json")["seconds"],
            "primary_episode_batches": sum(r["seconds"] for r in read("results/action_progress.json")),
            "diagnostic_method_batches": sum(r["seconds"] for r in read("results/diagnostic_progress.json"))
        },
        "timing_scope": "Accepted run, timed method batches only; excludes plotting, I/O between timers, profiling and the archived precision-fix attempt.",
        "no_additional_simulation": True
    }
    (ROOT / "results/report_numbers.json").write_text(
        json.dumps(numbers, ensure_ascii=False, indent=2), encoding="utf-8")
    packages = {}
    for name in ["numpy", "scipy", "torch", "numba", "matplotlib"]:
        packages[name] = importlib.metadata.version(name)
    (ROOT / "results/environment.json").write_text(json.dumps({
        "python": platform.python_version(), "platform": platform.platform(), "packages": packages,
        "execution": "GPU for six frozen encoder inferences; four CPU threads for rollout; zero training"
    }, indent=2), encoding="utf-8")
    # This also verifies the local snapshots used by this experiment, not just original files.
    for item in read("results/input_provenance.json"):
        # Original absolute paths are historical metadata; snapshots are authoritative here.
        assert digest(ROOT / item["snapshot"]) == item["sha256"]
    for name, value in read("results/preregistered_hashes.json").items():
        assert digest(ROOT / name) == value
    manifest = read("figures/manifest.json")
    for entry in manifest:
        for ext in ["png", "svg", "pdf"]:
            assert (ROOT / f"figures/{entry['figure']}.{ext}").is_file()
    selected = list(ROOT.glob("*.py")) + list(ROOT.glob("*.ps1")) + list(ROOT.glob("*.md"))
    selected += [ROOT / "config.json", ROOT / "eval.json"]
    selected += list((ROOT / "vendor").rglob("*.py"))
    selected += list((ROOT / "results").glob("*.json"))
    selected += list((ROOT / "raw").glob("*.npz"))
    selected += list((ROOT / "figures").glob("*.*"))
    hashes = {str(f.relative_to(ROOT)): digest(f) for f in sorted(set(selected))
              if f.name != "artifact_hashes.json"}
    (ROOT / "results/artifact_hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    print(json.dumps(numbers, ensure_ascii=False, indent=2))
    print(f"Verified 22 source/snapshot pairs and {len(manifest)} figures in all three formats.")

if __name__ == "__main__":
    run()

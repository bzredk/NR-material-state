"""Copy recorded data into the slide source without rerunning experiments."""
from pathlib import Path
import hashlib
import json
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / "2D/runs/information/channels_contact_20261026"
EXAMPLE = RUN / "test/test_5000/repeat_0/curves.npz"
HISTORY = RUN / "histories/test_5000.npz"
SUMMARY = RUN / "summary.json"
REFERENCE = ROOT.parent / "Documents/Codex/nadia-first-group-meeting-2026-10-22/output/10_1.pdf"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    curve = np.load(EXAMPLE)
    history = np.load(HISTORY)
    methods = ["basic_0.0", "lateral_0.0", "basic_0.2", "lateral_0.2",
               "basic_0.8", "lateral_0.8", "basic_contact", "lateral_contact", "replay", "truth"]
    actions = []
    for i, name in enumerate(["Slow press", "Fast press"]):
        truth = curve[f"truth_{i}_force"]
        actions.append({
            "name": name,
            "seconds": (curve[f"truth_{i}_time"] - curve[f"truth_{i}_time"][0]).tolist(),
            "methods": {
                m: {"force_mN": (curve[f"{m}_{i}_force"] * 1000).tolist(),
                    "error_mN": ((curve[f"{m}_{i}_force"] - truth) * 1000).tolist(),
                    "marker_um": (curve[f"{m}_{i}_markers"].mean(axis=1) * 1e6).tolist()}
                for m in methods
            }
        })
    data = {
        "summary": read(SUMMARY),
        "physics": read(RUN / "physics.json"),
        "example": {"parent_id": "test_5000", "repeat": 0, "actions": actions},
        "history": {
            "seconds": history["time"].tolist(),
            "force_mN": (curve["observed"][:, 2] * 1000).tolist(),
            "actual_d_mm": (history["d"] * 1000).tolist(),
            "command_mm": (history["command"] * 1000).tolist(),
            "marker_um": (curve["observed"][:, 3:5].mean(axis=1) * 1e6).tolist(),
            "phase": history["phase"].tolist(),
        },
        "coverage": [r for r in read(RUN / "coverage.json")
                     if r["parent_id"] == "test_5000" and r["repeat"] == 0],
        "reference": {"path": str(REFERENCE), "sha256": digest(REFERENCE)},
        "sources": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)}
                    for p in [SUMMARY, EXAMPLE, HISTORY, RUN / "coverage.json", RUN / "RESULTS.md"]],
    }
    (HERE / "assets").mkdir(exist_ok=True)
    (HERE / "assets/slide_data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("Prepared recorded curves and statistics for 24 independent histories.")

if __name__ == "__main__":
    main()

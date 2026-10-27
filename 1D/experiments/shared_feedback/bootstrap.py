"""Snapshot only required old artifacts. Never write to prior experiment trees."""
from pathlib import Path
import hashlib, json, shutil, difflib

ROOT = Path(__file__).resolve().parent
R3 = ROOT.parent / "02_transfer/v2"
R4 = ROOT.parent / "controller"
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    for d in ["vendor/round3", "vendor/round4", "inputs/checkpoints", "inputs/logs",
              "results", "raw", "figures", "logs"]:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    files = [(R3 / f, ROOT / "vendor/round3" / f)
             for f in ["models.py", "dynamics.py", "physics_base.py"]]
    files += [(R4 / f, ROOT / "vendor/round4" / f) for f in ["physics.py", "control.py"]]
    files += [(R3 / "config.json", ROOT / "inputs/round3_config.json"),
              (R3 / "fixed_material.json", ROOT / "inputs/fixed_material.json"),
              (R3 / "runs/transfer_v2/data/test_histories.npz", ROOT / "inputs/test_histories.npz"),
              (R4 / "results/test_contract_frozen.json", ROOT / "inputs/round4_contract.json"),
              (R4 / "results/reactive_tuning.json", ROOT / "inputs/round4_reactive.json")]
    for method in ["history_state", "snapshot_state"]:
        for seed in [11, 23, 47]:
            files += [
                (R3 / f"runs/transfer_v2/checkpoints/{method}_{seed}_best.pt",
                 ROOT / f"inputs/checkpoints/{method}_{seed}_best.pt"),
                (R3 / f"runs/transfer_v2/logs/{method}_{seed}_meta.json",
                 ROOT / f"inputs/logs/{method}_{seed}_meta.json")]
    records = []
    for src, dst in files:
        if dst.exists() and digest(src) != digest(dst):
            raise RuntimeError(f"Snapshot mismatch: {dst}")
        if not dst.exists():
            shutil.copy2(src, dst)
        records.append({"source": str(src), "snapshot": str(dst.relative_to(ROOT)), "sha256": digest(src)})
    original = (ROOT / "vendor/round4/control.py").read_text(encoding="utf-8")
    adapted = original.replace("keep_trace=False):", "keep_trace=False,initial_P=None):")
    adapted = adapted.replace("P=np.eye(2)*.0015**2;u=UMIN",
        "P=np.eye(2)*.0015**2 if initial_P is None else initial_P.copy();u=UMIN")
    assert adapted != original and "initial_P.copy()" in adapted
    (ROOT / "vendor/round4/control_bridge.py").write_text(adapted, encoding="utf-8")
    (ROOT / "results/control_adapter.diff").write_text(
        "".join(difflib.unified_diff(original.splitlines(True), adapted.splitlines(True),
                                    "round4/control.py", "bridge/control_bridge.py")), encoding="utf-8")
    save(ROOT / "results/input_provenance.json", records)
    save(ROOT / "results/preregistered_hashes.json",
         {f: digest(ROOT / f) for f in ["config.json", "eval.json"]})
    print(f"Preserved {len(records)} input artifacts; controller change: optional covariance input only.")

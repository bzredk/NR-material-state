"""Reproducible pilot orchestration, history-level splits and on-demand caches."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import importlib.metadata
import itertools
import json
import platform
import subprocess
import time
import traceback

import numpy as np

from .physics import Config, SpatialModel, Trace
from .protocols import protocol, future_commands
from .estimators import Observer, RESOLUTION, NOISE_STD, compare_predictions, history_sweep
from .checks import run_checks


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "2d_contact"


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def source_hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "src" / "nr2d").glob("*.py"))}


def signature(config):
    # Presentation changes do not invalidate numerical results.
    hashes = source_hashes()
    numeric = {k: hashes[k] for k in ("physics.py", "protocols.py", "estimators.py", "checks.py", "experiments.py")}
    payload = {"config": config.asdict(), "code": numeric, "seed": 20261026}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:12]


def environment():
    packages = {}
    for name in ("numpy", "scipy", "matplotlib", "pillow", "ipywidgets", "ipympl", "ipykernel", "nbformat", "nbclient"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "missing"
    def git(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()
    return {"python": platform.python_version(), "platform": platform.platform(), "processor": platform.processor(),
            "packages": packages, "git_head": git("rev-parse", "HEAD"), "git_status": git("status", "--short"),
            "source_sha256": source_hashes()}


def select_pair(histories, resolution=RESOLUTION):
    """Select lexicographically, using ONLY current deployable observations."""
    accepted = []
    attempts = []
    for a, b in itertools.combinations(sorted(histories), 2):
        residual = np.abs(histories[a].observation[-1] - histories[b].observation[-1])
        normalized = residual / resolution
        row = {"a": a, "b": b, "residual_SI": residual.tolist(), "normalized_residual": normalized.tolist(),
               "accepted": bool(np.all(normalized <= 1.))}
        attempts.append(row)
        if row["accepted"]:
            accepted.append(row)
    if not attempts:
        raise ValueError("At least two independent histories are required")
    selected = accepted[0] if accepted else min(attempts, key=lambda r: max(r["normalized_residual"]))
    return {"selected": selected, "selection_rule": "First lexicographic accepted pair; closest pair only if none accepts",
            "channels": ["actual indentation (m)", "actual velocity (m/s)", "force (N)", "left marker (m)", "right marker (m)"],
            "resolution_SI": resolution.tolist(), "resolution_status": "Synthetic planned sensor resolution, not measured",
            "attempted": len(attempts), "accepted": len(accepted), "acceptance_rate": len(accepted)/len(attempts),
            "attempts": attempts, "future_used_for_selection": False,
            "additional_matched_context": "Same command, elapsed time, robot/tool parameters, geometry and fixed material"}


def history_parameters(seed):
    rng = np.random.default_rng(seed)
    loading = float(rng.choice(np.arange(8, 17) * .03))
    return dict(amplitude=float(rng.uniform(.00028, .00043)), loading=loading,
                hold=round(.84-loading, 8), release=.26, wait=.30,
                excitation="pulse" if int(rng.integers(0, 2)) else "hold", include_future=False)


def load_histories(run, split=None):
    manifest = read_json(Path(run)/"manifest.json")
    return {h["id"]: Trace.load(Path(run)/h["path"]) for h in manifest["histories"]
            if h["status"] == "completed" and (split is None or h["split"] == split)}


def failure(run, context, exc):
    path = Path(run)/"failures.jsonl"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "context": context,
                                 "error": str(exc), "traceback": traceback.format_exc()})+"\n")


def forecasts_for(run, parent_id=None, action="Slow press", noise=0., force=False, progress=None):
    run = Path(run)
    pair = read_json(run/"matching.json")["selected"]
    parent_id = parent_id or pair["a"]
    slug = f"{parent_id}_{action.lower().replace(' ', '_')}_noise{noise:g}"
    out = run/"forecasts"/slug
    if not force and (out/"metrics.json").exists():
        metrics = read_json(out/"metrics.json")
        return {k: Trace.load(out/(k.lower().replace(" ", "_")+".npz")) for k in metrics}, metrics, "REPLAY: cached predictions"
    trace = load_histories(run)[parent_id]
    try:
        predictions, metrics = compare_predictions(SpatialModel(Config(**trace.config)), trace, action, noise, progress=progress)
        # Force recomputation keeps old numeric results in an audit subdirectory.
        if (out/"metrics.json").exists():
            backup = out/"previous"/datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup.mkdir(parents=True)
            for p in list(out.glob("*.json"))+list(out.glob("*.npz")):
                p.rename(backup/p.name)
        for name, tr in predictions.items():
            tr.metadata.update(parent_id=parent_id, noise_multiplier=noise, source="New spatial 2D solver")
            tr.save(out/(name.lower().replace(" ", "_")+".npz"))
        write_json(out/"metrics.json", metrics)
        write_json(out/"provenance.json", {"parent_id": parent_id, "action": action, "noise_multiplier": noise,
                   "noise_std_SI": (NOISE_STD*noise).tolist(), "seed": 123, "source_sha256": source_hashes(),
                   "utc": datetime.now(timezone.utc).isoformat(), "future_achieved_motion_given_to_predictors": False})
        return predictions, metrics, "RECOMPUTED: new solver predictions"
    except Exception as exc:
        failure(run, {"stage": "forecast", "parent": parent_id, "action": action, "noise": noise}, exc)
        raise


def sweep_for(run, excitation="hold", noise=0., force=False, progress=None):
    run = Path(run)
    path = run/"sweeps"/f"{excitation}_noise{noise:g}.json"
    if path.exists() and not force:
        return read_json(path), "REPLAY: cached history sweep"
    c = Config(**read_json(run/"config.json"))
    model = SpatialModel(c)
    commands, phases, _ = protocol(c, include_future=False, excitation=excitation)
    tr = model.simulate(commands, phases, metadata={"split": "validation", "parent_id": "sweep_"+excitation})
    try:
        rows = history_sweep(model, tr, noise=noise, progress=progress)
        tr.save(run/"sweeps"/(excitation+"_parent.npz"))
        if path.exists():
            backup = path.parent/"previous"/datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup.mkdir(parents=True)
            path.rename(backup/path.name)
        result = {"rows": rows, "excitation": excitation, "noise_multiplier": noise, "seed": 123,
                  "parent_path": f"sweeps/{excitation}_parent.npz", "split": "validation",
                  "status": "exploratory pilot; no test tuning or long-history claim", "source_sha256": source_hashes()}
        write_json(path, result)
        return result, "RECOMPUTED: new history sweep"
    except Exception as exc:
        failure(run, {"stage": "sweep", "excitation": excitation, "noise": noise}, exc)
        raise


def pair_refinement(run, progress=None):
    """Assess the selected pair's contrast at a finer mesh, without reselecting it."""
    run = Path(run)
    c = Config(**read_json(run/"config.json"))
    chosen = read_json(run/"matching.json")["selected"]
    manifest = read_json(run/"manifest.json")
    entries = {h["id"]: h for h in manifest["histories"]}
    output = {}
    for level, config in (("default", c), ("fine", replace(c, nx=c.nx*2, ny=c.ny*2))):
        model = SpatialModel(config)
        parents, futures = [], []
        for pid in (chosen["a"], chosen["b"]):
            if progress: progress(f"Pair contrast: {level}, {pid}")
            u, p, _ = protocol(config, **entries[pid]["parameters"])
            tr = model.simulate(u, p)
            commands, phases = future_commands(tr.checkpoint(), config, "Slow press")
            future = model.simulate(commands, phases, state=tr.checkpoint())
            future.save(run/"pair_refinement"/f"{level}_{pid}.npz")
            parents.append(tr); futures.append(future)
        output[level] = {"force_contrast_N": (futures[0].force-futures[1].force).tolist(),
                         "force_contrast_rms_N": float(np.sqrt(np.mean((futures[0].force-futures[1].force)**2))),
                         "current_residual_SI": np.abs(parents[0].observation[-1]-parents[1].observation[-1]).tolist(),
                         "matched_on_this_mesh": bool(np.all(np.abs(parents[0].observation[-1]-parents[1].observation[-1])<=RESOLUTION))}
    difference = np.array(output["default"]["force_contrast_N"])-output["fine"]["force_contrast_N"]
    output["contrast_discretization_rms_N"] = float(np.sqrt(np.mean(difference**2)))
    output["interpretation"] = "Local refinement check for this preselected pair; not a convergence proof or population estimate"
    write_json(run/"pair_refinement.json", output)
    return output


def run_pilot(config=Config(), force=False, progress=print):
    started = time.perf_counter()
    sig = signature(config)
    run = RUNS/f"pilot_{sig}"
    if not force and (run/"manifest.json").exists() and read_json(run/"manifest.json").get("status") == "completed":
        progress(f"REPLAY: verified cached spatial 2D pilot ({run.name})")
        return run, {"mode": "REPLAY", "wall_seconds": time.perf_counter()-started}
    if run.exists():
        run = RUNS/(run.name+"_"+datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    run.mkdir(parents=True)
    write_json(run/"config.json", config.asdict())
    manifest = {"status": "running", "created_utc": datetime.now(timezone.utc).isoformat(), "signature": sig,
                "environment": environment(), "histories": [], "failures": [], "statistical_unit": "Complete parent history",
                "sensor_resolution_SI": RESOLUTION.tolist(), "sensor_noise_std_SI": NOISE_STD.tolist(),
                "material_status": "Synthetic; no physical specimen calibration", "independent_test_history_count": 8,
                "known_parameters": True, "body_dynamics": "Quasistatic; dynamic 1-DOF indenter", "new_3d_or_hardware_evidence": False}
    write_json(run/"manifest.json", manifest)
    try:
        progress("RECOMPUTE 1/5: physics verification and main spatial sequence")
        checks, main = run_checks(config)
        main.metadata.update(source="New spatial 2D solver", split="calibration", parent_id="main_demonstration")
        main.save(run/"main.npz")
        write_json(run/"checks.json", checks)
        if not checks["passed"]:
            raise RuntimeError("Physical acceptance gate failed; results retained for diagnosis")
        model = SpatialModel(config)
        progress("RECOMPUTE 2/5: independent feasible histories; splits precede generation")
        for split, seeds in (("calibration", range(100, 103)), ("validation", range(200, 202)), ("test", range(300, 308))):
            for seed in seeds:
                pid = f"{split}_{seed}"
                params = history_parameters(seed)
                entry = {"id": pid, "seed": seed, "split": split, "parameters": params, "path": f"histories/{pid}.npz"}
                try:
                    u, p, _ = protocol(config, **params)
                    tr = model.simulate(u, p, metadata={"parent_id": pid, "split": split, "seed": seed, "parameters": params})
                    tr.save(run/entry["path"])
                    entry["status"] = "completed"
                except Exception as exc:
                    entry.update(status="failed", error=str(exc))
                    manifest["failures"].append(entry)
                    failure(run, entry, exc)
                manifest["histories"].append(entry)
        write_json(run/"manifest.json", manifest)
        matching = select_pair(load_histories(run, "test"))
        # Commit the matching record BEFORE any future branch is evaluated.
        write_json(run/"matching.json", matching)
        progress(f"Matching: {matching['accepted']}/{matching['attempted']} pairs accepted using current channels only")
        progress("RECOMPUTE 3/5: four estimators share the spatial future model")
        forecasts_for(run, progress=progress)
        progress("RECOMPUTE 4/5: validation history-window sweep")
        sweep_for(run, progress=progress)
        progress("RECOMPUTE 5/5: selected contrast under mesh refinement")
        pair_refinement(run, progress)
        manifest.update(status="completed", completed_utc=datetime.now(timezone.utc).isoformat(),
                        wall_seconds=time.perf_counter()-started, checks_passed=checks["passed"])
        write_json(run/"manifest.json", manifest)
        write_json(RUNS/"latest.json", {"run": str(run.relative_to(ROOT)), "signature": sig})
        return run, {"mode": "RECOMPUTED", "wall_seconds": manifest["wall_seconds"]}
    except Exception as exc:
        manifest.update(status="failed", error=str(exc), wall_seconds=time.perf_counter()-started)
        write_json(run/"manifest.json", manifest)
        failure(run, "pilot", exc)
        raise


def run_batch(run, actions=("Slow press", "Fast press"), noises=(0., 1.), progress=print):
    """Evaluate all test parents. Seeds/frames/branches are not independent samples."""
    start = time.perf_counter()
    rows = []
    for pid in sorted(load_histories(run, "test")):
        for action in actions:
            for noise in noises:
                progress(f"Batch: {pid}, {action}, noise={noise:g}")
                try:
                    _, metrics, mode = forecasts_for(run, pid, action, noise, progress=progress)
                    for method, values in metrics.items():
                        rows.append({"parent_id": pid, "action": action, "noise": noise, "method": method, **values})
                except Exception as exc:
                    rows.append({"parent_id": pid, "action": action, "noise": noise, "status": "failed", "error": str(exc)})
    result = {"rows": rows, "independent_units": len(load_histories(run, "test")), "wall_seconds": time.perf_counter()-start,
              "inference": "Descriptive pilot only; branches and noise realizations remain grouped within parents"}
    write_json(Path(run)/"batch.json", result)
    return result

"""First-data entry: preserve, inspect, summarize repeats, prepare constitutive fits.

No robot I/O, no new synthetic generation, and no automatic model training.
Controller context is joined causally on the declared common clock. This is
not a clock synchronization algorithm. Actual future motion is a conditioning
input for the explicitly labelled constitutive diagnostic, never a command forecast.
"""
import argparse
import collections
import copy
import hashlib
import math
import os
import shutil
import sys
from pathlib import Path

import numpy as np
from prepare_collection import ROOT, read_csv, read_json, write_csv, write_json, fresh_output
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
sys.path.insert(0, str(ROOT / "analysis_core"))
from real_data_intake import validate_rows
from pilot_io import load_dataset, splits, contact_position


def key(r):
    return r["session_id"], r["episode_id"]


def yes(value):
    return str(value).strip().lower() in {"true", "1"}


def join_controllers(normalized, schedule):
    """As-of join, never interpolate gains or read a later schedule row."""
    groups = collections.defaultdict(list)
    for row in schedule:
        r = dict(row)
        r["timestamp_s"] = float(r["timestamp_s"])
        if not math.isfinite(r["timestamp_s"]):
            raise ValueError("Nonfinite controller timestamp")
        for field in ["normal_stiffness_N_per_m", "normal_damping_Ns_per_m",
                      "command_update_hz", "force_sample_hz", "pose_sample_hz"]:
            if r.get(field, "") != "":
                value = float(r[field])
                allow_zero = field in {"normal_stiffness_N_per_m","normal_damping_Ns_per_m"}
                if not math.isfinite(value) or value < 0 or (not allow_zero and value == 0):
                    raise ValueError(f"Invalid {field} in controller schedule")
        seq = groups[key(r)]
        if seq and r["timestamp_s"] <= seq[-1]["timestamp_s"]:
            raise ValueError("Controller timestamps must increase within an episode; no silent sorting")
        groups[key(r)].append(r)
    normalized_keys = {key(r) for r in normalized}
    if set(groups) - normalized_keys:
        raise ValueError("Controller schedule contains an episode absent from raw.csv")
    missing = set()
    for r in normalized:
        seq = groups.get(key(r), [])
        j = np.searchsorted([s["timestamp_s"] for s in seq], r["timestamp_s"], side="right") - 1
        if j < 0:
            missing.add(key(r))
            continue
        for field, value in seq[j].items():
            if field not in {"session_id", "episode_id", "timestamp_s"}:
                r["controller__" + field] = value
        r["controller__source_time_s"] = seq[j]["timestamp_s"]
    return sorted("/".join(k) for k in missing)


def check_plans(rows):
    groups = collections.defaultdict(list)
    for r in rows:
        for field in ["command_time_s", "plan_available_time_s", "command_position_m"]:
            if not math.isfinite(float(r[field])):
                raise ValueError(f"Invalid command plan field {field}")
        if float(r["command_time_s"]) < float(r["plan_available_time_s"]):
            raise ValueError("A planned command cannot precede its plan's availability")
        if r["plan_kind"] != "precommitted_open_loop":
            raise ValueError("Future realized feedback commands are not a precommitted command plan")
        if r["interpolation"] not in {"linear", "zero_order_hold"}:
            raise ValueError("Declare command interpolation")
        groups[(*key(r), r["command_plan_id"])].append(r)
    for group in groups.values():
        if len({float(r["plan_available_time_s"]) for r in group}) != 1:
            raise ValueError("Each plan version needs one availability timestamp")
        if any(float(b["command_time_s"]) <= float(a["command_time_s"]) for a, b in zip(group, group[1:])):
            raise ValueError("Command knots must increase; no silent sorting")
    return len(groups)


def features(records, entry, meta):
    t = np.array([r["timestamp_s"] for r in records]); t -= t[0]
    x = np.array([r["actual_position_m"] for r in records])
    f = np.array([r["normal_force_N"] for r in records])
    u = np.array([r["command_position_m"] for r in records])
    ph = np.array([r["phase"] for r in records])
    base = ph == "baseline"; target = np.isin(ph, ["recontact", "rehold"])
    result = {k: entry.get(k, "") for k in ["session_id", "episode_id", "specimen_id", "role", "repeat", "program",
                                         "amplitude_m", "wait_s", "status", "reset_verified", "include_in_fit"]}
    result.update(actual_max_m=float(x.max()), tracking_rmse_m=float(np.sqrt(np.mean((x-u)**2))),
                  baseline_force_mean_N=float(f[base].mean()) if base.any() else None,
                  baseline_force_sd_N=float(f[base].std()) if base.any() else None)
    if target.sum() >= 2:
        result.update(recontact_peak_N=float(f[target].max()),
                      recontact_impulse_Ns=float(np.trapezoid(f[target], t[target])))
        config = meta.get("analysis", {})
        if config.get("contact_threshold_N") and config.get("contact_persistence_s"):
            cp = contact_position(t, x, f, ph, config["contact_threshold_N"], config["contact_persistence_s"])
            result["threshold_contact_m"] = cp
            threshold, persistence = config["contact_threshold_N"], config["contact_persistence_s"]
            def first_persistent(mask, signal_condition):
                for i in np.flatnonzero(mask):
                    end = np.searchsorted(t, t[i]+persistence)
                    if end < len(t) and np.all(signal_condition[i:end+1]):
                        return float(t[i])
                return None
            detached = first_persistent(np.isin(ph, ["retract","wait"]), np.abs(f) <= threshold)
            recontact = first_persistent(target, f > threshold)
            result["force_threshold_detach_time_s"] = detached
            result["force_threshold_recontact_time_s"] = recontact
            result["force_threshold_unloaded_interval_s"] = (
                recontact-detached if detached is not None and recontact is not None else None)
            waiting = ph == "wait"
            result["wait_samples_above_contact_threshold_fraction"] = (
                float(np.mean(np.abs(f[waiting]) > threshold)) if waiting.any() else None)
    return result


def repeat_metrics(selected, groups, features_by_key):
    cells = collections.defaultdict(list)
    for e in selected:
        cells[(e["program"], float(e["amplitude_m"]), float(e["wait_s"]))].append(e)
    result = []
    for condition, entries in sorted(cells.items()):
        if len(entries) != 2:
            continue
        e1, e2 = sorted(entries, key=lambda e: int(e["repeat"]))
        r1, r2 = groups[key(e1)], groups[key(e2)]
        rec = dict(program=condition[0], amplitude_m=condition[1], wait_s=condition[2],
                   episode_1=e1["episode_id"], episode_2=e2["episode_id"])
        f1, f2 = features_by_key[key(e1)], features_by_key[key(e2)]
        for field in ["recontact_peak_N", "recontact_impulse_Ns", "threshold_contact_m"]:
            a, b = f1.get(field), f2.get(field)
            rec["absolute_repeat_difference__" + field] = None if a is None or b is None else abs(a-b)
        # Align only by recorded recontact phase onset, not by response peaks.
        # No time warping; common duration only. This is descriptive variability.
        arrays = []
        for rr in [r1, r2]:
            rr = [r for r in rr if r["phase"] in {"recontact", "rehold"}]
            if len(rr) < 2:
                arrays = []
                break
            t = np.array([r["timestamp_s"] for r in rr]); t -= t[0]
            arrays.append((t, np.array([r["normal_force_N"] for r in rr])))
        if arrays:
            (t1, a), (t2, b) = arrays
            mask = t1 <= t2[-1]
            tt = t1[mask]
            if len(tt) > 1:
                err = a[mask] - np.interp(tt, t2, b)
                rec["repeat_force_rmse_N"] = float(np.sqrt(np.trapezoid(err**2, tt) / (tt[-1]-tt[0])))
        result.append(rec)
    return result


def inspect(dataset, output):
    folder = Path(dataset).resolve()
    out = fresh_output(output)
    raw_dir = out / "source"; raw_dir.mkdir()
    for filename in ["raw.csv", "metadata.json", "episodes.csv", "controller_schedule.csv",
                     "planned_commands.csv", "events.csv", "calibration_records.csv", "pretest_frozen.json"]:
        if (folder / filename).exists():
            shutil.copyfile(folder / filename, raw_dir / filename)
    meta = read_json(raw_dir / "metadata.json")
    rows = read_csv(raw_dir / "raw.csv")
    normalized, report = validate_rows(rows, meta)
    report["source_hashes"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in raw_dir.iterdir()}
    report["fit_ready"] = False
    report["pending"] = []
    report["fit_issues"] = []
    def fit_issue(message):
        report["fit_issues"].append(message)
        report["pending"].append(message)
    if report["status"] != "passed":
        write_json(out / "intake_report.json", report)
        raise ValueError("Raw time/unit validation failed; see intake_report.json; source retained")
    # Retain EVERY raw column without silently reinterpreting its units.
    for raw, norm in zip(rows, normalized):
        norm.update({"source__" + k: v for k, v in raw.items()})
    if (raw_dir / "controller_schedule.csv").exists():
        missing = join_controllers(normalized, read_csv(raw_dir / "controller_schedule.csv"))
        report["controller_context_missing_at_start"] = missing
    else:
        missing = sorted({"/".join(key(r)) for r in normalized})
        report["pending"].append("controller_schedule.csv missing: constitutive inspection possible; cross-control prediction not ready")
    if (raw_dir / "planned_commands.csv").exists():
        report["planned_command_versions"] = check_plans(read_csv(raw_dir / "planned_commands.csv"))
    else:
        report["pending"].append("planned_commands.csv missing: no future-command evidence yet")
    report["command_forecast_ready"] = False  # Requires independently validated coupled actuator, not just columns.
    write_csv(out / "normalized_with_context.csv", normalized)
    manifest = read_csv(raw_dir / "episodes.csv")
    mkeys = [key(e) for e in manifest]
    groups = collections.defaultdict(list)
    for r in normalized:
        groups[key(r)].append(r)
    if len(set(mkeys)) != len(mkeys):
        raise ValueError("Duplicate episode manifest key")
    # Planned but unrecorded rows are retained and listed, not treated as observations.
    report["unrecorded_planned"] = ["/".join(key(e)) for e in manifest if key(e) not in groups]
    if set(groups) - set(mkeys):
        raise ValueError("Unlisted raw episodes; add all attempts/anchors to episodes.csv")
    selected = []
    feature_rows = []
    for e in manifest:
        if key(e) not in groups:
            if e.get("status") == "complete":
                raise ValueError("Manifest says complete but no raw record: " + "/".join(key(e)))
            continue
        rr = groups[key(e)]
        if {r["specimen_id"] for r in rr} != {e["specimen_id"]}:
            raise ValueError("Specimen mismatch")
        observed = features(rr, e, meta)
        feature_rows.append(observed)
        if e.get("role", "core") != "core":
            continue
        if not yes(e.get("include_in_fit", "")):
            if not e.get("exclusion_reason", ""):
                fit_issue(f"{'/'.join(key(e))}: record fit disposition or exclusion reason")
            continue
        if e.get("status") != "complete":
            raise ValueError("Only completed trials can enter fits; retain other attempts")
        if not yes(e.get("reset_verified")):
            fit_issue(f"{'/'.join(key(e))}: no verified reset; current relaxed-start fitter cannot use it")
            continue
        if ("force_threshold_detach_time_s" in observed
                and observed["force_threshold_detach_time_s"] is None):
            fit_issue(f"{'/'.join(key(e))}: no persistent force-threshold detachment; inspect the attempted wait")
            continue
        selected.append(e)
    if feature_rows:
        write_csv(out / "episode_observables.csv", feature_rows)
    bykey = {key(e): e for e in feature_rows}
    repeats = repeat_metrics(selected, groups, bykey)
    if repeats:
        write_csv(out / "repeatability.csv", repeats)
    calibration = meta.get("calibration", {})
    names = ["force_bias_bound_N", "position_zero_bound_m", "time_alignment_bound_s",
             "local_stiffness_bound_N_m", "force_slew_bound_N_s"]
    bound = None
    if all(isinstance(calibration.get(k), (int, float)) and math.isfinite(calibration[k]) and calibration[k] >= 0 for k in names):
        bound = (calibration[names[0]] + calibration[names[1]]*calibration[names[3]]
                 + calibration[names[2]]*calibration[names[4]])
    repeat_values = [r["repeat_force_rmse_N"] for r in repeats if "repeat_force_rmse_N" in r]
    report["resolution_diagnostics"] = dict(
        conservative_force_calibration_sensitivity_N=bound,
        q90_paired_repeat_force_rmse_N=float(np.quantile(repeat_values, .9)) if repeat_values else None,
        interpretation="Descriptive screening scales, not statistical noise floors or confidence limits; no specimen replication")
    report["recorded_episodes"] = len(groups)
    report["selected_core_episodes"] = len(selected)
    if len(selected) == 24:
        if len({e.get("planned_id",e["episode_id"]) for e in selected}) != 24:
            raise ValueError("Multiple selected attempts of one planned trial; retain one predeclared QC-valid attempt")
        counts = collections.Counter((e["program"], float(e["amplitude_m"]), float(e["wait_s"])) for e in selected)
        expected = {(p, a, w) for p in ["slow", "overshoot"]
                    for a in {float(e["amplitude_m"]) for e in selected}
                    for w in {float(e["wait_s"]) for e in selected}}
        if len(expected) != 12 or set(counts) != expected or set(counts.values()) != {2}:
            raise ValueError("Core is not the balanced 2x2x3x2 design")
        for cell in counts:
            reps = {int(e["repeat"]) for e in selected if (e["program"], float(e["amplitude_m"]), float(e["wait_s"])) == cell}
            if reps != {1, 2}:
                raise ValueError("Each cell must contain technical repeats 1 and 2")
        if len({e["episode_id"] for e in selected}) != len(selected):
            raise ValueError("Use unique episode IDs across sessions to preserve prediction keys")
        analysis = meta.get("analysis", {})
        needed = ["reference_compression_m", "contact_threshold_N", "contact_persistence_s"]
        if meta["data_type"] == "real":
            needed += ["max_step_s", "tau_min_s", "tau_max_s"]
            if not meta.get("review", {}).get("calibration_reviewed"):
                fit_issue("Complete pretest calibration review before constitutive fitting")
        missing_params = [k for k in needed if not isinstance(analysis.get(k), (int, float))
                          or not math.isfinite(analysis[k]) or analysis[k] <= 0]
        if missing_params:
            report["pending"].append("Fill analysis settings: " + ", ".join(missing_params))
        elif analysis.get("tau_min_s") is not None and not analysis["tau_min_s"] < analysis["tau_max_s"]:
            report["pending"].append("tau_min_s must be less than tau_max_s")
        else:
            fitdir = out / "fit_dataset"; fitdir.mkdir()
            keys = {key(e) for e in selected}
            cols = meta.get("columns", {})
            chosen = [r for r in rows if (r[cols.get("session_id", "session_id")],
                                          r[cols.get("episode_id", "episode_id")]) in keys]
            write_csv(fitdir / "raw.csv", chosen)
            write_csv(fitdir / "episodes.csv", selected)
            fitmeta = copy.deepcopy(meta)
            fitmeta["analysis"]["constitutive_only"] = True
            write_json(fitdir / "metadata.json", fitmeta)
            try:
                episodes, _, _ = load_dataset(fitdir)
                split_records = {}
                for axis, pool, test in splits(episodes):
                    split_records[axis] = dict(
                        fit=[e["key"] for e in pool if int(e["repeat"]) == 1],
                        validation=[e["key"] for e in pool if int(e["repeat"]) == 2],
                        test=[e["key"] for e in test])
                write_json(out / "splits.json", split_records)
                report["fit_ready"] = not report["fit_issues"]
            except ValueError as exc:
                report["pending"].append(str(exc))
    else:
        report["pending"].append("Full condition-held-out fitting waits for 24 eligible core episodes; partial data inspection is complete")
    report["level"] = "pilot_screening_only"
    write_json(out / "intake_report.json", report)
    return report


def fit(inspected, output, models, axes, starts, max_nfev):
    folder = Path(inspected)
    report = read_json(folder / "intake_report.json")
    if not report["fit_ready"]:
        raise ValueError("Inspect report is not fit-ready; resolve its concrete pending data issues")
    out = fresh_output(output)
    from fit_evaluate import run
    run(folder / "fit_dataset", out, models, axes, starts, max_nfev)
    fits = read_json(out / "fits.json")
    metrics = read_csv(out / "metrics.csv")
    comparisons = []
    for axis in axes:
        available = [m for m in models if f"{axis}/{m}" in fits]
        for group, choices in [("fixed_law", [m for m in available if m[0] in {"L", "S", "Q"}]),
                               ("state_rate", [m for m in available if m in {"R2", "SR2"}])]:
            if not choices:
                continue
            def val(m):
                f = fits[f"{axis}/{m}"]
                return f["starts"][f["selected_start"]]["validation_phase_balanced_mse_N2"]
            winner = min(choices, key=val)
            selected = [r for r in metrics if r["axis"] == axis and r["model"] == winner and r["mode"] == "constitutive"]
            comparisons.append(dict(axis=axis, family=group, validation_selected_model=winner,
                                    validation_mse_N2=val(winner),
                                    test_mean_force_rmse_N=float(np.mean([float(r["force_rmse_N"]) for r in selected])),
                                    interpretation="Pilot descriptive comparison; test data did not select this family representative"))
    write_csv(out / "validation_selected_comparison.csv", comparisons)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("inspect"); q.add_argument("dataset"); q.add_argument("--output", required=True)
    q = sub.add_parser("fit"); q.add_argument("inspected"); q.add_argument("--output", required=True)
    q.add_argument("--models", nargs="+", default=["L2","L4","S2","S4","Q2","Q4","R2","SR2","L6","S6","Q6"])
    q.add_argument("--axes", nargs="+", choices=["amplitude","wait","program"], default=["amplitude","wait","program"])
    q.add_argument("--starts", type=int, default=2); q.add_argument("--max-nfev", type=int, default=250)
    a = p.parse_args()
    if a.command == "inspect":
        try:
            report = inspect(a.dataset, a.output)
        except Exception as exc:
            target = Path(a.output).resolve()
            if target.is_relative_to(ROOT) and (target/"source").exists() and not (target/"intake_report.json").exists():
                write_json(target/"intake_report.json",dict(status="failed",error=str(exc),raw_preserved=True,fit_ready=False))
            raise
        print({k: report[k] for k in ["status","recorded_episodes","selected_core_episodes","fit_ready","pending"]})
    else:
        print(fit(a.inspected, a.output, a.models, a.axes, a.starts, a.max_nfev))

"""Offline acquisition sheets. No robot connection and no automatic device defaults."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def write_csv(path, rows, fields=None):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fresh_output(path):
    out = Path(path).resolve()
    if not out.is_relative_to(ROOT):
        raise ValueError("Output must be inside this acquisition package")
    if out.exists() and any(out.iterdir()):
        raise ValueError("Use a new output directory; previous records are preserved")
    out.mkdir(parents=True, exist_ok=True)
    return out


NUMERIC = [
    "thickness_mm", "low_strain", "high_strain", "overshoot_factor",
    "preload_speed_mm_s", "retract_speed_mm_s", "probe_speed_mm_s",
    "hold_s", "rehold_s", "baseline_s", "air_position_m", "probe_target_m",
    "minimum_reset_wait_s", "reset_height_band_m", "reset_anchor_relative_band",
    "contact_threshold_N", "contact_persistence_s", "device_force_limit_N",
    "device_speed_limit_mm_s", "reversible_max_strain",
]
TEXT = ["specimen_id", "session_id", "pretest_record", "calibration_id",
        "controller_id", "reset_method", "freeze_date"]


def validate_settings(s):
    import math
    missing = [k for k in NUMERIC + TEXT + ["waits_s"] if s.get(k) in [None, ""]]
    if missing:
        raise ValueError("Fill from the pretest: " + ", ".join(missing))
    for k in NUMERIC:
        if not isinstance(s[k], (int, float)) or not math.isfinite(s[k]):
            raise ValueError(f"{k}: finite numeric value required")
        if k != "air_position_m" and s[k] <= 0:
            raise ValueError(f"{k}: positive value required")
    if not s["air_position_m"] < 0:
        raise ValueError("air_position_m must be negative in compression-positive coordinates")
    if not 0 < s["low_strain"] < s["high_strain"]:
        raise ValueError("Require 0 < low_strain < high_strain")
    if not 1 < s["overshoot_factor"]:
        raise ValueError("Overshoot must exceed the terminal amplitude")
    if not s["high_strain"] * s["overshoot_factor"] <= s["reversible_max_strain"] < 1:
        raise ValueError("All preload peaks must lie in the pretested reversible range")
    if s["probe_target_m"] > s["thickness_mm"] / 1000 * s["reversible_max_strain"]:
        raise ValueError("Common probe target is outside the pretested range")
    waits = s["waits_s"]
    if not isinstance(waits, dict) or set(waits) != {"short", "middle", "long"}:
        raise ValueError("waits_s needs short, middle, long")
    w = [waits[k] for k in ["short", "middle", "long"]]
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in w) or not 0 < w[0] < w[1] < w[2]:
        raise ValueError("Require three ordered positive waits")
    if max(s[k] for k in ["preload_speed_mm_s", "retract_speed_mm_s", "probe_speed_mm_s"]) > s["device_speed_limit_mm_s"]:
        raise ValueError("Planned speed exceeds the laboratory limit")
    if s["reset_anchor_relative_band"] >= 1:
        raise ValueError("Reset anchor band is a fraction, not a percentage")
    return s


def build_rows(settings=None):
    """Retain the already randomized order, not a redraw influenced by outcomes."""
    original = read_csv(ROOT / "references/original_protocol_24.csv")
    rows = []
    for r in original:
        row = dict(r)
        row.update(planned_id=r["episode_id"], role="core", attempt=1, status="planned",
                   include_in_fit="", exclusion_reason="", deviation="",
                   calibration_id="", controller_id="", command_plan_id="",
                   pretest_version="", actual_no_contact_wait_s="",
                   reset_height_error_m="", reset_anchor_relative_error="",
                   temperature_C="", recording_file="", operator="")
        row["notes"] = "Priority = H/overshoot/short; every factorial cell is retained"
        if settings:
            s = settings
            amp = s["thickness_mm"] / 1000 * s["low_strain" if r["amplitude_level"] == "L" else "high_strain"]
            row.update(session_id=s["session_id"], specimen_id=s["specimen_id"],
                       amplitude_m=amp, wait_s=s["waits_s"][r["wait_level"]],
                       calibration_id=s["calibration_id"], controller_id=s["controller_id"],
                       pretest_version=s["freeze_date"],
                       preload_peak_m=amp * (s["overshoot_factor"] if r["program"] == "overshoot" else 1),
                       hold_s=s["hold_s"], rehold_s=s["rehold_s"],
                       preload_speed_mm_s=s["preload_speed_mm_s"],
                       retract_speed_mm_s=s["retract_speed_mm_s"],
                       probe_speed_mm_s=s["probe_speed_mm_s"],
                       probe_target_m=s["probe_target_m"], air_position_m=s["air_position_m"],
                       minimum_reset_wait_s=s["minimum_reset_wait_s"],
                       # Optional zero-load lead-in equalizes time to terminal hold.
                       # The material is reset, so this delay does not preload it.
                       slow_zero_load_leadin_s=(2 * (s["overshoot_factor"]-1)*amp*1000/s["preload_speed_mm_s"]
                                               if r["program"] == "slow" else 0))
        rows.append(row)
    return rows


def make(output, settings=None):
    s = validate_settings(read_json(settings)) if settings else None
    out = fresh_output(output)
    rows = build_rows(s)
    write_csv(out / "collection_24.csv", rows)
    anchors = []
    for i, after in enumerate([0, 6, 12, 12, 18, 24], 1):
        anchors.append(dict(anchor_id=f"a{i:02d}", block=1 if i <= 3 else 2,
                            after_core_order=after, role="drift_reset_anchor",
                            program="frozen small-load reference", parameters="from pretest",
                            specimen_id=s["specimen_id"] if s else "",
                            session_id=s["session_id"] if s else "",
                            reset_again_before_next_core=True, status="planned", notes="Not one of the 24 core trials"))
    write_csv(out / "anchors_6.csv", anchors)
    control = [dict(control_trial_id=f"control{i+1:02d}", program=p, wait_level=w,
                    amplitude_level="one frozen pretest level", specimen_id="", role="fast_foam_control",
                    status="optional_planned") for i, (p, w) in enumerate(
                        (p, w) for p in ["slow", "overshoot"] for w in ["short", "middle", "long"])]
    write_csv(out / "optional_fast_foam_6.csv", control)
    write_json(out / "design_manifest.json", dict(
        status="parameterized_plan" if s else "symbolic_draft_not_device_settings",
        original_order_preserved=True, original_seed=20261019, allocation="two balanced randomized blocks of 12",
        order_source="references/original_protocol_24.csv",
        order_sha256=hashlib.sha256((ROOT / "references/original_protocol_24.csv").read_bytes()).hexdigest(),
        factorial="2 preload amplitudes x 2 history programs x 3 waits x 2 technical repeats",
        unit="one reset-to-recovery episode on one specimen", population_independent_replicates=1,
        priority_is_not_oversampling="H / overshoot / short",
        repeat_policy="retain every attempt; first QC-valid completed attempt per planned_id; no effect-based replacement",
        hardware_execution=False))
    if s:
        write_json(out / "pretest_frozen.json", s)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--settings", help="Filled pretest settings; omit to produce symbolic sheets")
    p.add_argument("--output", required=True)
    a = p.parse_args()
    print(make(a.output, a.settings))

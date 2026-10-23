"""Focused checks of new scheduling and assembly only; no model fitting/simulation."""
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import hashlib
import json
import shutil
import session as s
import first_batch

ROOT=Path(__file__).resolve().parent

def run():
    out=ROOT/"verification"/("interface_"+datetime.now().strftime("%Y%m%d_%H%M%S"))
    out.mkdir(parents=True)
    checks=[]
    try:
        s.resolve(ROOT/"session_plan/parameter_form.csv")
        raise AssertionError("Blank pretest form unexpectedly executable.")
    except ValueError:
        checks.append("Blank physical settings rejected.")

    # Interface-only finite numbers; never used to generate material responses.
    values=dict(specimen_id="TEST_ONLY",session_id="TEST_ONLY",pretest_record="NOT_LAB_SETTINGS",
        calibration_id="TEST_ONLY",controller_id="TEST_ONLY",reset_method="reference_washout",
        freeze_date="TEST_ONLY",thickness_mm=20,low_strain=.1,high_strain=.2,overshoot_factor=1.3,
        preload_speed_mm_s=2,retract_speed_mm_s=3,probe_speed_mm_s=2,hold_s=10,rehold_s=8,
        baseline_s=2,air_position_m=-.001,probe_target_m=.004,minimum_reset_wait_s=60,
        reset_anchor_relative_band=.05,contact_threshold_N=.1,contact_persistence_s=.1,
        device_force_limit_N=20,device_speed_limit_mm_s=5,reversible_max_strain=.4)
    values.update({"waits_s.short":1,"waits_s.middle":3,"waits_s.long":10,
        "session.handling_per_record_s":15,"session.anchor_target_m":.001,
        "session.anchor_hold_s":3,"session.anchor_speed_mm_s":1})
    rows=s.form_rows()
    for row in rows:
        if row["key"] in values:row["value"]=values[row["key"]]
    form=out/"TEST_ONLY_parameter_values.csv";s.write(form,rows)
    params,admin=s.resolve(form)
    assert params["reset_height_band_m"] is None
    plan=s.plan(out/"TEST_ONLY_nominal_plan",params,admin)
    core=s.read(plan/"protocol_24.csv");order=s.read(plan/"run_order_30.csv")
    source=s.read(ROOT/"references/original_protocol_24.csv")
    for a,b in zip(core,source):
        for k in ["episode_id","repeat","program","amplitude_level","wait_level","order"]:
            assert a[k]==b[k],k
    assert len(order)==30 and sum(x["role"]=="core" for x in order)==24
    for block in [1,2]:
        sub=[r for r in core if int(r["block"])==block]
        assert len({(r["program"],r["amplitude_level"],r["wait_level"]) for r in sub})==12
    seg=s.read(plan/"motion_segments_relative.csv")
    by=defaultdict(list)
    for row in seg:by[row["episode_id"]].append(row)
    for A in ["L","H"]:
        pair=[r for r in core if r["amplitude_level"]==A and r["wait_level"]=="short" and r["repeat"]=="1"]
        holds=[float(next(z["start_relative_s"] for z in by[r["episode_id"]] if z["phase"]=="hold")) for r in pair]
        assert abs(holds[0]-holds[1])<1e-10
    assert all(r.get("forecast_start_s","")=="" for r in core)
    assert all(float(r["reset_after_s"])==60 for r in order)
    checks.append("Original 24-row order, balanced blocks, six anchors, matched hold start and actual-event blanks preserved.")
    checks.append("Reference washout accepts an unmeasured optical band; no fake height supplied.")
    bad=[dict(r) for r in rows]
    for r in bad:
        if r["key"]=="probe_speed_mm_s":r["value"]=50
    s.write(out/"TEST_ONLY_invalid.csv",bad)
    try:
        s.resolve(out/"TEST_ONLY_invalid.csv");raise AssertionError("Invalid speed accepted.")
    except ValueError:checks.append("Entered speed limit enforced.")

    # Replay existing raw files from the prior package; do not synthesize new data.
    original=ROOT/"verification/fixture_source"
    prepared=out/"existing_fixture";prepared.mkdir()
    for name in ["metadata.json","episodes.csv","controller_schedule.csv"]:
        shutil.copy2(original/name,prepared/name)
    raw=s.read(original/"raw.csv");groups=defaultdict(list)
    for row in raw:groups[row["episode_id"]].append(row)
    recordings=out/"existing_recordings";recordings.mkdir()
    for eid,rr in groups.items():s.write(recordings/f"{eid}.csv",rr)
    assembled=s.assemble(prepared,recordings,out/"assembled")
    assert len(s.read(assembled/"raw.csv"))==len(raw)
    first_batch.inspect(assembled,out/"inspected")
    report=json.loads((out/"inspected/intake_report.json").read_text())
    assert report["fit_ready"] and report["selected_core_episodes"]==24
    assert not report["command_forecast_ready"]
    checks.append("Existing synthetic fixture: all raw rows retained; unchanged first_batch accepts assembled 24-row batch.")
    checks.append("Constitutive-ready does not claim command-forecast readiness.")
    preserved=True
    for item in json.loads((ROOT/"source_manifest.json").read_text()):
        # Validate the included frozen copy independently of the original workstation.
        preserved &= hashlib.sha256((ROOT/item["copy"]).read_bytes()).hexdigest()==item["sha256"]
    assert preserved
    result=dict(status="passed",checks=checks,source_copies_unchanged=True,
        fixture="pre-existing synthetic_validation raw files only",
        no_new_material_simulation=True,no_model_fit=True,actual_lab_settings_filled=False,
        detailed_records=str(out.relative_to(ROOT)))
    s.dump(ROOT/"verification/interface_report.json",result)
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    run()

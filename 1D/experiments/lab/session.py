"""First-session planning and CSV assembly. No robot connection or model fitting."""
import argparse
import copy
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path
import prepare_collection as old

ROOT = Path(__file__).resolve().parent
ADMIN = {
    "booking_minutes": 300,
    "preparation_budget_minutes": 110,
    "between_blocks_minutes": 10,
    "handoff_minutes": 15,
    "contingency_minutes": 30,
    "handling_per_record_s": None,
    "anchor_target_m": None,
    "anchor_hold_s": None,
    "anchor_speed_mm_s": None,
}
WHY = {
    "thickness_mm": "Measure relaxed specimen, before the formal block",
    "low_strain": "Distinct low terminal preload; fractional strain, not percent",
    "high_strain": "Informative repeatable terminal preload",
    "overshoot_factor": "Peak / terminal preload; high peak remains recoverable",
    "hold_s": "Common terminal hold after both history programs",
    "rehold_s": "Common post-wait probe hold",
    "air_position_m": "Negative clearance relative to the fixed relaxed surface",
    "probe_target_m": "One common future compression target for all 24",
    "minimum_reset_wait_s": "Washout after return to clearance; validated after worst preload",
    "reset_method": "optical_and_reference OR reference_washout",
    "reset_height_band_m": "Required only for optical_and_reference; otherwise leave blank",
    "reset_anchor_relative_band": "Fraction; measured repeat band of small reference response",
    "preload_speed_mm_s": "Both programs use the same resolved ramp speed",
    "waits_s.short": "Dwell at clearance; account separately for departure/approach time",
    "waits_s.middle": "Intermediate recovery dwell; held out in the wait split",
    "waits_s.long": "Late recovery dwell, not assumed to equal full reset",
}

def read(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write(path, rows, fields=None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fields=fields or list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def dump(path, value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")

def fresh(path):
    out=Path(path).resolve()
    if not out.is_relative_to(ROOT):
        raise ValueError("Keep session outputs inside this new project.")
    if out.exists() and any(out.iterdir()):
        raise ValueError("Use a new output directory; existing records are preserved.")
    out.mkdir(parents=True,exist_ok=True)
    return out

def form_rows():
    template=old.read_json(ROOT/"templates/pretest_settings.json")
    rows=[]
    for k,v in template.items():
        if k=="note":continue
        for key in ([f"waits_s.{x}" for x in ["short","middle","long"]] if isinstance(v,dict) else [k]):
            units=("mm/s" if key.endswith("_mm_s") else
                   "s" if key.startswith("waits_s.") or key.endswith("_s") else "mm" if key.endswith("_mm") else
                   "m" if key.endswith("_m") else "N" if key.endswith("_N") else
                   "fraction" if "strain" in key or "band" in key else "text" if key in old.TEXT else "ratio")
            rows.append(dict(key=key,value="",unit=units,
                basis=WHY.get(key,"Enter the measured/pretested value or lab configuration"),
                evidence_file="",entered_by=""))
    for k,v in ADMIN.items():
        rows.append(dict(key="session."+k,value="" if v is None else v,
            unit="min" if "minutes" in k else "mm/s" if k.endswith("_mm_s") else
                 "m" if k.endswith("_m") else "s",
            basis="Booking budget only; editable, not a device setting" if v is not None else
                  "Small reference probe / practical handling measured during pretest",
            evidence_file="",entered_by=""))
    return rows

def resolve(path):
    rows=read(path);expected={r["key"] for r in form_rows()}
    if len(rows)!=len({r["key"] for r in rows}):raise ValueError("Duplicate parameter keys.")
    if {r["key"] for r in rows}!=expected:raise ValueError("Parameter keys differ from the supplied form.")
    s={};a={}
    for r in rows:
        k,v=r["key"],r["value"].strip()
        if not v:value=None
        elif k in old.TEXT:value=v
        else:
            value=float(v)
            if not math.isfinite(value):raise ValueError("Nonfinite parameter: "+k)
        if k.startswith("waits_s."):s.setdefault("waits_s",{})[k.split(".")[1]]=value
        elif k.startswith("session."):a[k.split(".",1)[1]]=value
        else:s[k]=value
    # Same original checks, except an unmeasured optical reset band is not mandatory
    # for the explicitly named reference-response washout route.
    if s.get("reset_method") not in {"optical_and_reference","reference_washout"}:
        raise ValueError("Choose optical_and_reference or reference_washout reset_method.")
    numeric=[k for k in old.NUMERIC if k!="reset_height_band_m"]
    for k in numeric+old.TEXT:
        if s.get(k) in [None,""]:raise ValueError("Fill from pretest/configuration: "+k)
    for k in numeric:
        if k!="air_position_m" and s[k]<=0:raise ValueError("Positive value required: "+k)
    band=s.get("reset_height_band_m")
    if s["reset_method"]=="optical_and_reference" and (band is None or band<=0):
        raise ValueError("Optical reset requires a measured positive height band.")
    if band is not None and band<=0:raise ValueError("Height band must be positive or unmeasured.")
    if not s["air_position_m"]<0:raise ValueError("Clearance must be negative.")
    if not 0<s["low_strain"]<s["high_strain"]:raise ValueError("Need low < high.")
    if not s["overshoot_factor"]>1:raise ValueError("Overshoot factor must exceed 1.")
    if not s["high_strain"]*s["overshoot_factor"]<=s["reversible_max_strain"]<1:
        raise ValueError("High overshoot exceeds the pretested recoverable range.")
    maximum=s["thickness_mm"]*.001*s["reversible_max_strain"]
    if s["probe_target_m"]>maximum:raise ValueError("Common probe outside pretested range.")
    w=[s["waits_s"][x] for x in ["short","middle","long"]]
    if any(x is None for x in w) or not 0<w[0]<w[1]<w[2]:raise ValueError("Need short < middle < long.")
    if s["reset_anchor_relative_band"]>=1:raise ValueError("Reference band must be a fraction.")
    if any(v is None or v<=0 for v in a.values()):raise ValueError("Complete positive session/anchor settings.")
    if a["anchor_target_m"]>s["thickness_mm"]*.001*s["low_strain"]:
        raise ValueError("Reference anchor should not exceed the low preload.")
    speeds=[s[k] for k in ["preload_speed_mm_s","retract_speed_mm_s","probe_speed_mm_s"]]+[a["anchor_speed_mm_s"]]
    if max(speeds)>s["device_speed_limit_mm_s"]:raise ValueError("Speed exceeds entered laboratory limit.")
    return s,a

def trajectory(row,s,a):
    """Ideal relative plan for timing/documentation, not robot-ready commands.

    Acceleration/jerk/interpolation and observed transitions remain the lab's responsibility.
    Reset is included in the last recovery segment; no extra touch is hidden in it.
    """
    air=s["air_position_m"];v=s["preload_speed_mm_s"]*.001;vr=s["retract_speed_mm_s"]*.001
    u=air;t=0.;segments=[]
    def segment(phase,substage,duration,target):
        nonlocal t,u
        if duration<=1e-12:return
        segments.append(dict(episode_id=row["episode_id"],phase=phase,substage=substage,
            start_relative_s=t,end_relative_s=t+duration,command_start_relative_m=u,
            command_end_relative_m=target,coordinate="compression_positive_from_fixed_relaxed_surface",
            status="timing_reference_not_device_command"))
        u=target;t+=duration
    segment("baseline","unloaded_recording",s["baseline_s"],air)
    if row["role"]=="core":
        A=row["amplitude_m"];peak=row["preload_peak_m"]
        segment("baseline","matched_unloaded_leadin",row["slow_zero_load_leadin_s"],air)
        segment("preload","rise",abs(peak-air)/v,peak)
        segment("preload","return_from_overshoot",abs(peak-A)/v,A)
        segment("hold","common_terminal_hold",s["hold_s"],A)
        forecast=t
        segment("retract","withdraw",abs(A-air)/vr,air)
        segment("wait","dwell_at_clearance",row["wait_s"],air)
        target=s["probe_target_m"]
        segment("recontact","common_probe",abs(target-air)/(s["probe_speed_mm_s"]*.001),target)
        segment("rehold","common_probe_hold",s["rehold_s"],target)
    else:
        target=a["anchor_target_m"]
        segment("preload","small_reference_rise",abs(target-air)/(a["anchor_speed_mm_s"]*.001),target)
        segment("hold","small_reference_hold",a["anchor_hold_s"],target)
        forecast=""
    segment("recovery","final_withdraw",abs(target-air)/vr,air)
    active=t
    segment("recovery","washout_for_next_record",s["minimum_reset_wait_s"],air)
    return segments,active,t,forecast

def plan(out,s=None,a=None):
    out=fresh(out);core=old.build_rows(s)
    rows=[];anchor=0
    def add_anchor(block):
        nonlocal anchor
        anchor+=1
        r={k:"" for k in core[0]}
        r.update(episode_id=f"a{anchor:02d}",planned_id=f"a{anchor:02d}",repeat=0,
                 role="drift_reset_anchor",program="anchor",block=block,status="planned",
                 include_in_fit="false",attempt=1,exclusion_reason="Reference probe; not one of the 24 core trials")
        if s:r.update(specimen_id=s["specimen_id"],session_id=s["session_id"],
                      amplitude_m=a["anchor_target_m"],wait_s=0,
                      calibration_id=s["calibration_id"],controller_id=s["controller_id"])
        rows.append(r)
    for block in [1,2]:
        add_anchor(block)
        for i,r in enumerate(core[(block-1)*12:block*12],1):
            r["block"]=block;rows.append(r)
            if i in [6,12]:add_anchor(block)
    write(out/"protocol_24.csv",core)
    allsegments=[];schedule=[]
    elapsed=(a["preparation_budget_minutes"]+s["minimum_reset_wait_s"]/60) if s else None
    first_block_end=None
    for i,r in enumerate(rows,1):
        iscore=r["role"]=="core"
        cond=f'{r["amplitude_level"]}/{r["program"]}/{r["wait_level"]}' if iscore else "same small reference"
        item=dict(run_order=i,block=r["block"],episode_id=r["episode_id"],core_order=r.get("order",""),
            condition=cond,role=r["role"],
            scientific_role="complete amplitude x history x wait cell" if iscore else "drift and reset evidence",
            priority_display="yes" if cond=="H/overshoot/short" else "no",
            reset_before="verified washout from previous record",
            active_nominal_s="",reset_after_s="",handling_s="",planned_start_min="",planned_end_min="",
            actual_start_common_s="",actual_end_common_s="",status="planned",deviation="")
        if s:
            segments,active,cycle,forecast=trajectory(r,s,a);allsegments+=segments
            r["planned_forecast_start_s"]=forecast
            # forecast_start_s intentionally remains blank: record the actual retract event.
            item.update(active_nominal_s=round(active,3),reset_after_s=s["minimum_reset_wait_s"],
                handling_s=a["handling_per_record_s"],planned_start_min=round(elapsed,2))
            elapsed+=(cycle+a["handling_per_record_s"])/60
            item["planned_end_min"]=round(elapsed,2)
            if r["episode_id"]=="a03":
                first_block_end=elapsed
                elapsed+=a["between_blocks_minutes"]
        schedule.append(item)
    write(out/"run_order_30.csv",schedule)
    batch=out/"data";batch.mkdir()
    write(batch/"episodes.csv",rows)
    for name in ["raw.csv","metadata.json","controller_schedule.csv","planned_commands.csv",
                 "events.csv","calibration_records.csv","pretest_observations.csv"]:
        shutil.copy2(ROOT/"templates"/name,batch/name)
    if s:
        write(out/"motion_segments_relative.csv",allsegments)
        dump(batch/"pretest_frozen.json",s)
        dump(out/"session_parameters_frozen.json",a)
        m=old.read_json(batch/"metadata.json")
        m["analysis"].update(reference_compression_m=s["probe_target_m"],
            contact_threshold_N=s["contact_threshold_N"],contact_persistence_s=s["contact_persistence_s"])
        m["calibration"]["calibration_id"]=s["calibration_id"]
        m["acquisition"]["pretest_freeze"]="pretest_frozen.json"
        dump(batch/"metadata.json",m)
        total=elapsed+a["handoff_minutes"]+a["contingency_minutes"]
        budget=dict(total_nominal_minutes=round(total,1),booking_minutes=a["booking_minutes"],
            full_24_nominally_fit=total<=a["booking_minutes"],
            block1_including_3_anchors_and_reset_end_min=round(first_block_end,1),
            block1_plus_handoff_contingency_min=round(first_block_end+a["handoff_minutes"]+a["contingency_minutes"],1),
            interpretation="Nominal linear-path timing. Acceleration limits, confirmation and retries may add time; do not shorten washout to meet the booking.",
            initial_reset_s=s["minimum_reset_wait_s"],records=30,
            counted="One initial washout + each record's active path, post-record washout and handling; one between-block break.")
        dump(out/"time_budget.json",budget)
    dump(out/"plan_manifest.json",dict(status="resolved_offline_plan" if s else "symbolic_awaiting_pretest",
        original_order_preserved=True,source_sha256=hashlib.sha256((ROOT/"references/original_protocol_24.csv").read_bytes()).hexdigest(),
        core=24,anchors=6,blocks=2,technical_repeats=2,independent_specimens=1,
        controller="one fixed actual lab configuration; no simulation settings copied",
        wait_definition="scheduled dwell at clearance; measured full no-contact interval reported separately",
        device_execution=False))
    return out

def assemble(prepared,recordings,out):
    """Combine one CSV per attempt; retain all records, never sort samples or infer QC."""
    prepared=Path(prepared).resolve();recordings=Path(recordings).resolve()
    data=prepared/"data" if (prepared/"data").exists() else prepared
    episodes=read(data/"episodes.csv");keys={(r["session_id"],r["episode_id"]):r for r in episodes}
    files=sorted(recordings.glob("*.csv"))
    if not files:raise ValueError("No per-attempt CSV recordings.")
    samples=[];seen=set();provenance=[]
    required={"episode_id","specimen_id","session_id","timestamp","command_position","actual_position","normal_force","phase"}
    for file in files:
        rr=read(file)
        if not rr or not required.issubset(rr[0]):raise ValueError("Missing core fields in "+file.name)
        ids={(r["session_id"],r["episode_id"]) for r in rr}
        if len(ids)!=1:raise ValueError("Use one CSV per actual attempt: "+file.name)
        k=next(iter(ids))
        if k in seen:raise ValueError("An episode occurs in more than one recording; resolve chunks explicitly.")
        seen.add(k)
        if k not in keys:raise ValueError("Register all attempts/anchors in episodes.csv: "+str(k))
        if {r["specimen_id"] for r in rr}!={keys[k]["specimen_id"]}:raise ValueError("Specimen mismatch.")
        samples+=rr
        provenance.append(dict(file=file.name,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),rows=len(rr)))
    # Use the unchanged original unit/time checker, not a new interpretation.
    from analysis_core.real_data_intake import validate_rows
    meta=old.read_json(data/"metadata.json")
    _,qc=validate_rows(samples,meta)
    if qc["status"]!="passed":raise ValueError("Resolve time/unit errors before assembly: "+str(qc["errors"]))
    output=fresh(out)
    for file in data.iterdir():
        if file.is_file() and file.name!="raw.csv":shutil.copy2(file,output/file.name)
    write(output/"raw.csv",samples)
    source=output/"original_recordings";source.mkdir()
    for file in files:shutil.copy2(file,source/file.name)
    dump(output/"assembly_manifest.json",dict(recordings=provenance,quality=qc,
        auto_selected_for_fitting=False,missing_plans=[list(k) for k in keys if k not in seen]))
    return output

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="command",required=True)
    z=sub.add_parser("init");z.add_argument("--output",required=True)
    z=sub.add_parser("build");z.add_argument("--parameters",required=True);z.add_argument("--output",required=True)
    z=sub.add_parser("assemble");z.add_argument("--prepared",required=True);z.add_argument("--recordings",required=True);z.add_argument("--output",required=True)
    args=p.parse_args()
    if args.command=="init":
        out=plan(args.output);write(out/"parameter_form.csv",form_rows())
    elif args.command=="build":
        s,a=resolve(args.parameters);out=plan(args.output,s,a)
        shutil.copy2(args.parameters,out/"parameter_form_frozen.csv")
    else:out=assemble(args.prepared,args.recordings,args.output)
    print(out)

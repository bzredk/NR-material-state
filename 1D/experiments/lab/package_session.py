"""Package offline handoff assets, excluding test-only parameter values and caches."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
if __name__=="__main__":
    source=json.loads((ROOT/"source_manifest.json").read_text())
    for item in source:
        assert hashlib.sha256(Path(item["source"]).read_bytes()).hexdigest()==item["sha256"]
        assert hashlib.sha256((ROOT/item["copy"]).read_bytes()).hexdigest()==item["sha256"]
    report=json.loads((ROOT/"verification/interface_report.json").read_text())
    assert report["status"]=="passed"
    files=[]
    for p in ROOT.rglob("*"):
        if not p.is_file():continue
        rel=p.relative_to(ROOT)
        if any(x in {"__pycache__",".cache","collection","recordings","runs","figures"} for x in rel.parts):continue
        if rel.parts[0]=="verification" and rel.name!="interface_report.json":continue
        if p.suffix==".zip" or p.name=="package_manifest.json":continue
        files.append(p)
    manifest=dict(status="offline_ready_actual_values_pending_pretest",source_files_preserved=len(source),
        core_trials=24,reference_anchors=6,independent_formal_specimens=1,
        numerical_device_defaults=False,no_real_data_collected=True,no_new_simulation_or_training=True,
        excluded="Test-only example settings, old synthetic fixture copies, caches and QA raster.",
        files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)})
    (ROOT/"package_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    files.append(ROOT/"package_manifest.json")
    output=ROOT/"Nadia_first_session_2026-10-20.zip"
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):
            z.write(p,"Nadia_first_session_2026-10-20/"+str(p.relative_to(ROOT)).replace("\\","/"))
    with zipfile.ZipFile(output) as z:assert z.testzip() is None
    print(f"Packaged {len(files)} files; {output.stat().st_size/1024:.1f} KiB.")

"""Copy only reusable acquisition assets; never change the earlier package."""
from pathlib import Path
import hashlib, json, shutil

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "acquisition"
FILES = [
    "prepare_collection.py", "first_batch.py", "plot_intake.py", "requirements.txt",
    "references/original_protocol_24.csv", "eval.json",
    *[f"analysis_core/{n}.py" for n in
      ["pilot_io", "mechanisms", "fit_evaluate", "plot_analysis", "real_data_intake"]],
]

if __name__ == "__main__":
    files = FILES + [str(p.relative_to(SOURCE)) for p in (SOURCE/"templates").glob("*") if p.is_file()]
    records = []
    for name in files:
        src, dst = SOURCE/name, ROOT/name
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise FileExistsError(dst)
        shutil.copy2(src, dst)
        records.append(dict(source=str(src), copy=name,
                            sha256=hashlib.sha256(src.read_bytes()).hexdigest()))
    (ROOT/"source_manifest.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Copied {len(records)} existing assets; no earlier file changed.")

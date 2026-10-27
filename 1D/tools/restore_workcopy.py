"""Restore a compact workcopy snapshot without overwriting an existing directory."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
from archive_paths import resolve_recorded_path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inside(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError(f"Path escapes its root: {relative}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    names={"history-dependence":"e1", "controller-transfer":"e2", "shared-feedback":"e3", "material-collection":"lab"}
    aliases={value:key for key,value in names.items()}
    parser.add_argument("--experiment", type=lambda value: aliases.get(value,value), choices=names, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    archive = args.archive.resolve()
    target = args.destination.resolve()
    if not archive.is_relative_to(ROOT) or not target.is_relative_to(ROOT):
        parser.error("Archive and destination must stay inside this project.")
    if target.exists():
        parser.error("Destination exists. Choose a new directory.")
    manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
    records = manifest["workcopies"][names[args.experiment]]["files"]
    with zipfile.ZipFile(archive / "overrides.zip") as store:
        def content(row):
            if "source" in row:
                return resolve_recorded_path(row["source"]).read_bytes()
            return store.read(row["object"])

        target.mkdir(parents=True)
        for row in records:
            dest = inside(target, row["path"])
            data = content(row)
            if digest(data) != row["sha256"]:
                raise ValueError(f"Retained source changed: {row['path']}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
    print(json.dumps({"status": "passed", "experiment": args.experiment,
                      "files": len(records), "destination": str(target)}))


if __name__ == "__main__":
    main()

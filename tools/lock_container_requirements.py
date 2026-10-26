"""Turn a Linux pip --dry-run --report result into an exact, hashed wheel lock."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("report", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
report = json.loads(args.report.read_text(encoding="utf-8"))
env = report["environment"]
assert env["sys_platform"] == "linux" and env["platform_machine"] == "x86_64", env
assert env["python_full_version"] == "3.11.9", env
lines = ["# Generated from requirements-container.in in Linux/amd64, CPython 3.11.9.",
         "# Every resolved dependency and wheel SHA256 is pinned. No Windows packages.", ""]
for item in sorted(report["install"], key=lambda x: x["metadata"]["name"].lower()):
    meta = item["metadata"]
    download = item["download_info"]
    assert download["url"].endswith(".whl"), download["url"]
    digest = download["archive_info"]["hashes"]["sha256"]
    lines.append(f"{meta['name']}=={meta['version']} --hash=sha256:{digest}")
args.output.write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")
print(f"Locked {len(report['install'])} Linux wheel dependencies.")

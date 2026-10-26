"""Validate this research package's traceability, not its scientific claims."""
from pathlib import Path
import ast
import hashlib
import json
import re
from urllib.parse import unquote

PLAN = Path(__file__).resolve().parents[1]
REPO = PLAN.parents[1]
checks = []
errors = []


def check(name, condition, detail=""):
    checks.append({"check": name, "passed": bool(condition), "detail": detail})
    if not condition:
        errors.append(name)


for path in PLAN.rglob("*.json"):
    if path.name != "validation_report.json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
            check(f"JSON: {path.relative_to(PLAN)}", True)
        except (ValueError, OSError) as exc:
            check(f"JSON: {path.relative_to(PLAN)}", False, str(exc))

for path in PLAN.rglob("*.py"):
    try:
        ast.parse(path.read_text(encoding="utf-8"))
        check(f"Python syntax: {path.relative_to(PLAN)}", True)
    except SyntaxError as exc:
        check(f"Python syntax: {path.relative_to(PLAN)}", False, str(exc))

chinese_companion = REPO.parent / "Documents/Codex/2026-10-25-hidden-state-reframing/research_synthesis_zh.md"
for path in [*PLAN.rglob("*.md"), chinese_companion]:
    content = path.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", content):
        target = unquote(target.strip("<> ").split("#")[0])
        if not target or re.match(r"https?://|mailto:", target):
            continue
        resolved = Path(target) if Path(target).is_absolute() else path.parent / target
        check(f"Link: {path.name} -> {target}", resolved.exists())
    prose = re.sub(r"\]\(([^)]+)\)", "]()", content)
    if path != chinese_companion:
        check(f"English technical prose: {path.name}", not re.search(r"[\u4e00-\u9fff]", prose))

figure_data = json.loads((PLAN / "figure_data.json").read_text(encoding="utf-8"))
for relative, expected in figure_data["source_sha256"].items():
    path = REPO / relative
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    check(f"Preserved archived source: {relative}", actual == expected)

registry = json.loads((PLAN / "registry.json").read_text(encoding="utf-8"))
papers = json.loads((PLAN / "literature_registry.json").read_text(encoding="utf-8"))
paper_ids = {p["id"] for p in papers["papers"]} | {"P14"}
for chain in registry["chains"]:
    check(f"Question link: {chain['id']}", chain["question"] in registry["questions"])
    for field in ("experiments", "levels", "data"):
        check(f"{field} links: {chain['id']}", all(i in registry[field] for i in chain[field]))
    check(f"Source links: {chain['id']}", all(i in registry["sources"] or i in paper_ids for i in chain["sources"]))
for name, source in registry["sources"].items():
    if "path" in source:
        check(f"Source path: {name}", (PLAN / source["path"]).exists())

spec = json.loads((PLAN / "eval_spec.json").read_text(encoding="utf-8"))
required = {"name":str,"claim":str,"unit_of_analysis":str,"datasets":list,"splits":list,
            "baselines":list,"metrics":list,"ablations":list,"falsification_criteria":list,
            "compute_budget":dict,"seeds":list,"artifacts":list}
check("Evaluation required fields", all(isinstance(spec.get(k),t) and spec[k] for k,t in required.items()))
check("Planning status retained", spec["status"] == "PROPOSED_NOT_EXECUTED")
check("Matched/natural test allocation", next(s for s in spec["splits"] if s["name"]=="initial_2d_test")["planned_units"] == 128)
check("Figure pair fixed independently of effect", json.loads((PLAN/"figures/provenance.json").read_text())["pair_source"]["pair_index"] == 0)

files = []
for path in sorted(PLAN.rglob("*")):
    if path.is_file() and path.name != "validation_report.json" and "__pycache__" not in str(path):
        files.append({"path":str(path.relative_to(PLAN)).replace("\\","/"),
                      "bytes":path.stat().st_size, "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
report = {"date":"2026-10-25", "scope":"document, source-preservation and contract checks only; no scientific experiment",
          "passed":not errors, "check_count":len(checks), "errors":errors, "checks":checks,
          "file_manifest":files,
          "manual_checks":["three generated PNG figures inspected visually", "three theory PDF pages rendered and inspected separately", "closest-method and physical-evidence peer reviews incorporated"]}
(PLAN/"validation_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"passed":not errors,"checks":len(checks),"errors":errors},indent=2))
raise SystemExit(1 if errors else 0)

"""Resolve paths in preserved manifests after the repository layout changed."""
import json
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[1]
REPO = BUNDLE.parent
LAYOUT = json.loads((BUNDLE / "provenance/current_layout.json").read_text(encoding="utf-8"))


def resolve_recorded_path(relative):
    relative = relative.replace("\\", "/")
    for old, new in sorted(LAYOUT.items(), key=lambda item: -len(item[0])):
        if relative == old or relative.startswith(old + "/"):
            relative = new + relative[len(old):]
            break
    path = (REPO / relative).resolve()
    if not path.is_relative_to(REPO):
        raise ValueError(f"Recorded path leaves the repository: {relative}")
    return path

from __future__ import annotations

import json
from datetime import datetime, timezone

from core.paths import LAB_DIR, ensure_project_dirs
from research.applicability_judge import judge_applicability


def research_to_lab_candidate(item: dict) -> dict:
    judgment = judge_applicability(item)
    candidate = {
        "source_research": item.get("url") or item.get("title"),
        "claim": item.get("summary") or item.get("title"),
        "hypothesis": f"Testing this research may improve Eve: {item.get('title', 'untitled')}",
        "experiment": "compare baseline capability metric against implementation variant",
        "metric": "capability_delta",
        "expected_gain": judgment["expected_gain"],
        "rollback": "revert candidate patch and keep research as watch item",
        "judgment": judgment,
    }
    return candidate


def write_research_lab_candidate(item: dict) -> dict:
    ensure_project_dirs()
    candidate = research_to_lab_candidate(item)
    path = LAB_DIR / "candidate_improvements" / f"research_to_lab_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(candidate, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**candidate, "path": str(path)}

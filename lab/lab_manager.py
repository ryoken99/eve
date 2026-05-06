from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from core.paths import LAB_DIR, ensure_project_dirs


def create_candidate(title: str, hypothesis: str, metric: str = "manual_review") -> Path:
    ensure_project_dirs()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in title.lower()).strip("_")
    path = LAB_DIR / "candidate_improvements" / f"{safe}.json"
    payload = {
        "title": title,
        "hypothesis": hypothesis,
        "metric": metric,
        "status": "candidate",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "decision": None,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def list_candidates() -> list[str]:
    ensure_project_dirs()
    return sorted(p.stem for p in (LAB_DIR / "candidate_improvements").glob("*.json"))

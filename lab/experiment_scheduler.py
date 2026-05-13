from __future__ import annotations

import json
from datetime import datetime, timezone

from core.paths import LAB_DIR, ensure_project_dirs


def schedule_experiment(candidate: dict) -> dict:
    ensure_project_dirs()
    payload = {
        "hypothesis": candidate["hypothesis"],
        "baseline": candidate.get("baseline", ""),
        "variant": candidate.get("variant", ""),
        "metric": candidate["metric"],
        "threshold": candidate.get("threshold", 0.0),
        "decision": "planned",
        "rollback": candidate.get("rollback", ""),
        "evidence": [],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    path = LAB_DIR / "experiments" / f"scheduled_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**payload, "path": str(path)}

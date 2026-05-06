from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import LAB_DIR, ensure_project_dirs
from security.audit_log import log_event


def create_experiment(title: str, hypothesis: str, metric: str, procedure: str) -> Path:
    ensure_project_dirs()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in title.lower()).strip("_")
    path = LAB_DIR / "experiments" / f"{safe}.json"
    payload = {
        "title": title,
        "hypothesis": hypothesis,
        "metric": metric,
        "procedure": procedure,
        "status": "planned",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "result": None,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log_event("lab_experiment_created", {"path": str(path), "title": title})
    return path


def record_experiment_result(experiment_name: str, result: str, decision: str) -> Path:
    path = LAB_DIR / "experiments" / f"{experiment_name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Experiencia nao encontrada: {experiment_name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["status"] = "completed"
    payload["result"] = result
    payload["decision"] = decision
    payload["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log_event("lab_experiment_completed", {"path": str(path), "decision": decision})
    return path

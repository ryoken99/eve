from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import STATE_DIR, ensure_project_dirs
from security.audit_log import log_event


SCHEDULE_PATH = STATE_DIR / "scheduled_tasks.json"


def _load() -> list[dict]:
    if not SCHEDULE_PATH.exists():
        return []
    try:
        return json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(tasks: list[dict]) -> Path:
    ensure_project_dirs()
    SCHEDULE_PATH.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
    return SCHEDULE_PATH


def add_scheduled_task(name: str, cadence: str, action: str, enabled: bool = True) -> Path:
    tasks = _load()
    tasks.append(
        {
            "name": name,
            "cadence": cadence,
            "action": action,
            "enabled": enabled,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "last_run": None,
        }
    )
    path = _save(tasks)
    log_event("scheduled_task_added", {"name": name, "cadence": cadence, "action": action})
    return path


def list_scheduled_tasks() -> list[dict]:
    return _load()

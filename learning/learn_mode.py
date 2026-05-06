from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs
from learning.skill_manager import create_draft_skill
from security.audit_log import log_event


def demonstration_path(name: str) -> Path:
    ensure_project_dirs()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.lower()).strip("_")
    return MEMORY_DIR / "procedural" / "demonstrations" / f"{safe}.json"


def record_demonstration(name: str, description: str, steps: list[dict]) -> Path:
    path = demonstration_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": name,
        "description": description,
        "steps": steps,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "manual_text_v0",
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log_event("demonstration_recorded", {"path": str(path), "name": name})
    return path


def create_skill_from_demonstration(name: str, description: str, steps: list[dict]) -> Path:
    record_demonstration(name, description, steps)
    return create_draft_skill(name, description, steps)

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import LOGS_DIR, ensure_project_dirs


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def audit_log_path() -> Path:
    ensure_project_dirs()
    return LOGS_DIR / "audit" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"


def log_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "timestamp": now_iso(),
        "event_type": event_type,
        "payload": payload,
    }
    with audit_log_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry

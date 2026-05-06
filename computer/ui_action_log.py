from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import LOGS_DIR, ensure_project_dirs


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def log_ui_action(action: str, payload: dict) -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "ui_actions" / f"{datetime.now().date().isoformat()}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": now_iso(), "action": action, **payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path

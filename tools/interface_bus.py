from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import LOGS_DIR, ensure_project_dirs


INTERFACE_INBOX_PATH = LOGS_DIR / "interface_inbox.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def publish_interface_message(source: str, content: str, *, target: str = "Sandro", tags: list[str] | None = None) -> dict:
    ensure_project_dirs()
    entry = {
        "timestamp": now_iso(),
        "source": source,
        "target": target,
        "content": content,
        "tags": tags or [],
    }
    with INTERFACE_INBOX_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry

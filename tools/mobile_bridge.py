from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import EVE_ROOT, ensure_project_dirs


BRIDGE_DIR = EVE_ROOT / "mobile_bridge"
INBOX = BRIDGE_DIR / "inbox.jsonl"
OUTBOX = BRIDGE_DIR / "outbox.jsonl"


def bridge_status() -> dict:
    ensure_project_dirs()
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    return {"bridge_dir": str(BRIDGE_DIR), "inbox": str(INBOX), "outbox": str(OUTBOX)}


def queue_mobile_message(message: str) -> Path:
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "message": message}
    with OUTBOX.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return OUTBOX

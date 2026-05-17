from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


EVE_ROOT = Path(__file__).resolve().parents[1]
SESSION_ROOT = EVE_ROOT / "memory" / "runtime" / "sessions"
ACTIVE_DIR = SESSION_ROOT / "active"
ARCHIVE_DIR = SESSION_ROOT / "archive"
HANDOFF_DIR = SESSION_ROOT / "handoffs"
STATE_DIR = SESSION_ROOT / "state"
LATEST_HANDOFF_PATH = HANDOFF_DIR / "latest_handoff.md"
CURRENT_SESSION_PATH = STATE_DIR / "current_session.json"

DEFAULT_HANDOFF_CHARS = 2500


def ensure_session_dirs() -> None:
    for path in (ACTIVE_DIR, ARCHIVE_DIR, HANDOFF_DIR, STATE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_latest_handoff(max_chars: int = DEFAULT_HANDOFF_CHARS) -> str:
    ensure_session_dirs()
    if not LATEST_HANDOFF_PATH.exists():
        return ""
    text = LATEST_HANDOFF_PATH.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 80)].rstrip() + "\n\n[handoff truncated to context limit]"


def handoff_metadata() -> dict[str, Any]:
    ensure_session_dirs()
    if not LATEST_HANDOFF_PATH.exists():
        return {"exists": False, "path": str(LATEST_HANDOFF_PATH)}
    stat = LATEST_HANDOFF_PATH.stat()
    age_seconds = max(0, int(datetime.now().timestamp() - stat.st_mtime))
    return {
        "exists": True,
        "path": str(LATEST_HANDOFF_PATH),
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "age_seconds": age_seconds,
    }

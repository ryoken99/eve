import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import LOGS_DIR, MEMORY_DIR, ensure_project_dirs
from security.safety_modes import current_safety_mode


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def diary_path(day: str | None = None) -> Path:
    return MEMORY_DIR / "diary" / f"{day or today_key()}.md"


def chat_log_path(day: str | None = None) -> Path:
    return LOGS_DIR / "chat" / f"{day or today_key()}.jsonl"


def append_chat(role: str, content: str, *, session_id: str = "main", mode: str | None = None, tags: list[str] | None = None) -> dict[str, Any]:
    ensure_project_dirs()
    entry = {
        "timestamp": now_iso(),
        "source": "chat",
        "role": role,
        "content": content,
        "session_id": session_id,
        "mode": mode or current_safety_mode(),
        "tags": tags or [],
    }
    with chat_log_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    md = diary_path()
    if not md.exists():
        md.write_text(f"# Eve Diary {today_key()}\n\n", encoding="utf-8")
    with md.open("a", encoding="utf-8") as fh:
        fh.write(f"## {entry['timestamp']} - {role}\n\n{content}\n\n")
    return entry


def read_diary(day: str | None = None) -> str:
    path = diary_path(day)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def list_diary_days() -> list[str]:
    ensure_project_dirs()
    return sorted(p.stem for p in (MEMORY_DIR / "diary").glob("*.md"))

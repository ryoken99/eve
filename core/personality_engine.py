from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs


PREF_PATH = MEMORY_DIR / "personality" / "evolving_preferences.md"


def add_preference(preference: str, reason: str = "") -> Path:
    ensure_project_dirs()
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with PREF_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"\n- {timestamp}: {preference.strip()}")
        if reason.strip():
            handle.write(f" | razao: {reason.strip()}")
        handle.write("\n")
    return PREF_PATH


def read_preferences() -> str:
    if not PREF_PATH.exists():
        return ""
    return PREF_PATH.read_text(encoding="utf-8")

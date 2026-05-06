from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from computer.active_window import get_active_window_title
from computer.vision import describe_screen
from core.paths import MEMORY_DIR, ensure_project_dirs


APP_PROFILE_DIR = MEMORY_DIR / "procedural" / "apps"


def capture_app_profile(name: str | None = None) -> Path:
    ensure_project_dirs()
    APP_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    title = get_active_window_title()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (name or title or "app").lower()).strip("_")
    observation = describe_screen(use_ocr=True)
    payload = {
        "name": name or title,
        "window_title": title,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "observation": observation,
        "known_targets": [],
        "skills": [],
    }
    path = APP_PROFILE_DIR / f"{safe}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def list_app_profiles() -> list[str]:
    ensure_project_dirs()
    APP_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(path.stem for path in APP_PROFILE_DIR.glob("*.json"))

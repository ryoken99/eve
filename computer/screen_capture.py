from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pyautogui

from computer.ui_action_log import log_ui_action
from core.paths import LOGS_DIR, ensure_project_dirs


def screenshot_dir() -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "ui_actions" / "screenshots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def take_screenshot(name: str | None = None) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_name = name or f"screen_{timestamp}"
    if not safe_name.lower().endswith(".png"):
        safe_name = f"{safe_name}.png"
    path = screenshot_dir() / safe_name
    image = pyautogui.screenshot()
    image.save(path)
    log_ui_action("screenshot", {"path": str(path)})
    return path


def screen_size() -> tuple[int, int]:
    return pyautogui.size()

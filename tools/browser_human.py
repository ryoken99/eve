from __future__ import annotations

import os
import urllib.parse
from pathlib import Path

from computer.keyboard_control import hotkey, press_key, type_text
from computer.screen_capture import take_screenshot
from computer.ui_action_log import log_ui_action
from computer.visual_executor import run_visual_steps
from core.paths import LOGS_DIR, ensure_project_dirs


def _normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("URL vazia")
    if "://" not in value:
        return "https://" + value
    return value


def open_url(url: str) -> dict:
    ensure_project_dirs()
    normalized = _normalize_url(url)
    before = take_screenshot("before_open_url")
    os.startfile(normalized)
    after = take_screenshot("after_open_url")
    payload = {"url": normalized, "before": str(before), "after": str(after)}
    log_ui_action("browser_open_url", payload)
    return payload


def search_web(query: str) -> dict:
    encoded = urllib.parse.urlencode({"q": query.strip()})
    return open_url(f"https://www.google.com/search?{encoded}")


def navigate_address_bar(url: str) -> dict:
    normalized = _normalize_url(url)
    before = take_screenshot("before_navigate_address_bar", scope="all")
    hotkey("ctrl", "l")
    type_text(normalized)
    press_key("enter")
    after = take_screenshot("after_navigate_address_bar", scope="all")
    payload = {"url": normalized, "before": str(before), "after": str(after)}
    log_ui_action("browser_navigate_address_bar", payload)
    return payload


def browser_visual_task(steps: list[dict]) -> dict:
    return run_visual_steps(steps)


def log_browser_note(kind: str, content: str) -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "browser" / "browser_human_notes.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {kind}\n\n{content.strip()}\n")
    return path

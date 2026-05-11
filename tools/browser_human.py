from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.parse
from pathlib import Path

from computer.keyboard_control import hotkey, press_key, type_text
from computer.monitors import list_monitors
from computer.screen_capture import take_screenshot
from computer.ui_action_log import log_ui_action
from computer.visual_executor import run_visual_steps
from core.paths import CONFIG_DIR, LOGS_DIR, ensure_project_dirs


BROWSER_CONFIG = CONFIG_DIR / "browser.json"
DEFAULT_CHROME_PATHS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]


def _default_browser_config() -> dict:
    chrome_path = next((str(path) for path in DEFAULT_CHROME_PATHS if path.exists()), "chrome.exe")
    return {
        "browser": "google_chrome",
        "profile_name": "eve",
        "profile_directory": "Profile 2",
        "chrome_path": chrome_path,
        "user_data_dir": str(Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"),
        "new_window": True,
        "target_monitor_index": 2,
        "window_margin": 40,
    }


def browser_config() -> dict:
    ensure_project_dirs()
    if not BROWSER_CONFIG.exists():
        BROWSER_CONFIG.write_text(json.dumps(_default_browser_config(), indent=2, ensure_ascii=False), encoding="utf-8")
    config = _default_browser_config()
    config.update(json.loads(BROWSER_CONFIG.read_text(encoding="utf-8")))
    return config


def _target_monitor(config: dict, monitors: list[dict] | None = None) -> dict | None:
    monitors = monitors if monitors is not None else list_monitors()
    if not monitors:
        return None
    target_index = config.get("target_monitor_index")
    for monitor in monitors:
        if monitor.get("index") == target_index:
            return monitor
    return monitors[-1]


def browser_launch_args(url: str, *, config: dict | None = None, monitors: list[dict] | None = None) -> list[str]:
    config = config or browser_config()
    normalized = _normalize_url(url)
    args = [
        config.get("chrome_path") or "chrome.exe",
        f"--profile-directory={config['profile_directory']}",
    ]
    user_data_dir = config.get("user_data_dir")
    if user_data_dir:
        args.append(f"--user-data-dir={user_data_dir}")
    if config.get("new_window", True):
        args.append("--new-window")

    monitor = _target_monitor(config, monitors)
    if monitor:
        margin = int(config.get("window_margin", 40))
        width = max(800, int(monitor["width"]) - margin * 2)
        height = max(600, int(monitor["height"]) - margin * 2)
        args.append(f"--window-position={int(monitor['left']) + margin},{int(monitor['top']) + margin}")
        args.append(f"--window-size={width},{height}")

    args.append(normalized)
    return args


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
    config = browser_config()
    before = take_screenshot("before_open_url", scope="all")
    args = browser_launch_args(normalized, config=config)
    try:
        subprocess.Popen(args)
    except FileNotFoundError:
        os.startfile(normalized)
    time.sleep(4)
    after = take_screenshot("after_open_url", scope="all")
    payload = {
        "url": normalized,
        "browser": config["browser"],
        "profile_name": config["profile_name"],
        "profile_directory": config["profile_directory"],
        "before": str(before),
        "after": str(after),
    }
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
    time.sleep(3)
    after = take_screenshot("after_navigate_address_bar", scope="all")
    payload = {"url": normalized, "before": str(before), "after": str(after)}
    log_ui_action("browser_navigate_address_bar", payload)
    return payload


def close_browser_page(reason: str = "task_finished") -> dict:
    before = take_screenshot("before_close_browser_page", scope="all")
    action = hotkey("ctrl", "w")
    time.sleep(1)
    after = take_screenshot("after_close_browser_page", scope="all")
    payload = {
        "status": "closed_requested",
        "reason": reason,
        "method": "ctrl+w",
        "before": str(before),
        "after": str(after),
        "action": action,
    }
    log_ui_action("browser_close_page", payload)
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

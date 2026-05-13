from __future__ import annotations

from datetime import datetime
from pathlib import Path

try:
    import pyautogui
except Exception:  # pragma: no cover - optional GUI dependency fallback
    pyautogui = None
try:
    from PIL import ImageGrab
except Exception:  # pragma: no cover - optional GUI dependency fallback
    ImageGrab = None

from computer.monitors import list_monitors, virtual_bounds
from computer.ui_action_log import log_ui_action
from core.paths import LOGS_DIR, ensure_project_dirs


def screenshot_dir() -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "ui_actions" / "screenshots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_name(name: str | None, scope: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    stem = name or f"screen_{scope}"
    safe_name = f"{stem}_{timestamp}"
    if not safe_name.lower().endswith(".png"):
        safe_name = f"{safe_name}.png"
    return safe_name


def take_screenshot(name: str | None = None, *, scope: str = "primary", monitor_index: int | None = None) -> Path:
    safe_name = _safe_name(name, scope)
    path = screenshot_dir() / safe_name
    metadata: dict = {"path": str(path), "scope": scope}
    if pyautogui is None or ImageGrab is None:
        path.write_bytes(b"")
        metadata["screen_available"] = False
        log_ui_action("screenshot_unavailable", metadata)
        return path
    if scope == "all":
        image = ImageGrab.grab(all_screens=True)
        metadata["bounds"] = virtual_bounds()
    elif scope == "monitor":
        monitors = list_monitors()
        if monitor_index is None:
            monitor_index = 0
        monitor = monitors[monitor_index]
        bbox = (monitor["left"], monitor["top"], monitor["right"], monitor["bottom"])
        image = ImageGrab.grab(bbox=bbox)
        metadata["monitor"] = monitor
        metadata["bounds"] = monitor
    else:
        image = pyautogui.screenshot()
        metadata["bounds"] = {"left": 0, "top": 0, "width": image.width, "height": image.height}
    image.save(path)
    log_ui_action("screenshot", metadata)
    return path


def screen_size() -> tuple[int, int]:
    if pyautogui is None:
        return (0, 0)
    return pyautogui.size()


def capture_desktop() -> dict:
    path = take_screenshot(scope="all")
    return {"screenshot": str(path), "bounds": virtual_bounds(), "monitors": list_monitors()}


def capture_monitor(index: int) -> dict:
    path = take_screenshot(scope="monitor", monitor_index=index)
    monitors = list_monitors()
    return {"screenshot": str(path), "monitor": monitors[index]}

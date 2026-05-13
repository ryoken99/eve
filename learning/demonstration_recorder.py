from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from pynput import keyboard, mouse
except Exception:  # pragma: no cover - optional recorder dependency fallback
    keyboard = None
    mouse = None

from computer.screen_capture import take_screenshot
from core.paths import MEMORY_DIR, ensure_project_dirs
from security.audit_log import log_event


def record_user_demonstration(name: str, duration_seconds: int = 30, description: str = "") -> Path:
    ensure_project_dirs()
    path = MEMORY_DIR / "procedural" / "demonstrations" / f"{name}.events.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    events: list[dict] = []
    started = time.time()
    before = take_screenshot(f"demo_{name}_before", scope="all")
    if keyboard is None or mouse is None:
        after = take_screenshot(f"demo_{name}_after", scope="all")
        payload = {
            "name": name,
            "description": description,
            "mode": "event_recording_unavailable",
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "duration_seconds": 0,
            "before_screenshot": str(before),
            "after_screenshot": str(after),
            "events": [],
            "error": "pynput nao esta instalado",
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        log_event("demonstration_events_unavailable", {"path": str(path)})
        return path

    def stamp() -> float:
        return round(time.time() - started, 3)

    def on_click(x, y, button, pressed):
        events.append({"t": stamp(), "type": "mouse_click", "x": x, "y": y, "button": str(button), "pressed": pressed})

    def on_scroll(x, y, dx, dy):
        events.append({"t": stamp(), "type": "mouse_scroll", "x": x, "y": y, "dx": dx, "dy": dy})

    def on_press(key):
        events.append({"t": stamp(), "type": "key_press", "key": str(key)})

    def on_release(key):
        events.append({"t": stamp(), "type": "key_release", "key": str(key)})

    mouse_listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)
    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    mouse_listener.start()
    keyboard_listener.start()
    time.sleep(max(1, duration_seconds))
    mouse_listener.stop()
    keyboard_listener.stop()
    after = take_screenshot(f"demo_{name}_after", scope="all")
    payload = {
        "name": name,
        "description": description,
        "mode": "event_recording_v1",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "duration_seconds": duration_seconds,
        "before_screenshot": str(before),
        "after_screenshot": str(after),
        "events": events,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log_event("demonstration_events_recorded", {"path": str(path), "events": len(events)})
    return path


def summarize_demonstration(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for event in payload.get("events", []):
        counts[event["type"]] = counts.get(event["type"], 0) + 1
    return {"name": payload.get("name"), "duration_seconds": payload.get("duration_seconds"), "event_counts": counts}

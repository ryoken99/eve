from __future__ import annotations

from datetime import datetime, timezone

from computer.active_window import get_active_window_title
from computer.vision import describe_screen
from tools.browser_playwright import browser_dom_snapshot
from computer.uia_observer import dump_active_window_tree


def capture_environment_state(*, include_screen: bool = False, include_uia: bool = True, include_browser: bool = True) -> dict:
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "active_window": get_active_window_title(),
    }
    if include_browser:
        state["browser"] = browser_dom_snapshot()
    if include_uia:
        state["uia"] = dump_active_window_tree(max_depth=2)
    if include_screen:
        state["screen"] = describe_screen(use_ocr=True, scope="visible")
    return state

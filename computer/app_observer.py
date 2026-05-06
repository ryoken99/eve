from __future__ import annotations

from computer.active_window import get_active_window_title
from computer.vision import describe_screen
from security.audit_log import log_event


def observe_active_app() -> dict:
    observation = describe_screen(use_ocr=True)
    observation["app_title"] = get_active_window_title()
    log_event("active_app_observed", {"app_title": observation["app_title"], "screenshot": observation["screenshot"]})
    return observation

from __future__ import annotations

from computer.mouse_control import click
from computer.vision import describe_screen, first_text_center, find_text_on_screen
from security.audit_log import log_event


def click_text_and_verify(text: str, verify_text: str | None = None) -> dict:
    before = describe_screen(use_ocr=True)
    target = first_text_center(text)
    if not target.get("found"):
        result = {"status": "target_not_found", "target": text, "before": before, "target_result": target}
        log_event("visual_click_text_failed", result)
        return result
    action = click(int(target["x"]), int(target["y"]))
    after = describe_screen(use_ocr=True)
    verification = None
    if verify_text:
        verification = find_text_on_screen(verify_text)
    result = {
        "status": "clicked",
        "target": text,
        "coordinates": {"x": target["x"], "y": target["y"]},
        "action": action,
        "before_screenshot": before["screenshot"],
        "after_screenshot": after["screenshot"],
        "verification": verification,
    }
    log_event("visual_click_text", result)
    return result

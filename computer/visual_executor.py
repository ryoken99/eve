from __future__ import annotations

from computer.keyboard_control import hotkey, press_key, type_text
from computer.mouse_control import click
from computer.vision import describe_screen, find_text_on_screen, first_text_center
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


def run_visual_steps(steps: list[dict], *, stop_on_error: bool = True) -> dict:
    transcript = []
    initial = describe_screen(use_ocr=True)
    for index, step in enumerate(steps, start=1):
        action = step.get("action")
        try:
            if action == "click_text":
                result = click_text_and_verify(step["text"], step.get("verify_text"))
            elif action == "type_text":
                result = type_text(step["text"])
            elif action == "press_key":
                result = press_key(step["key"])
            elif action == "hotkey":
                result = hotkey(*step["keys"])
            elif action == "verify_text":
                result = find_text_on_screen(step["text"])
                result["status"] = "verified" if result.get("found") else "not_found"
            else:
                raise ValueError(f"Acao visual desconhecida: {action}")
            transcript.append({"index": index, "step": step, "result": result})
            if result.get("status") in {"target_not_found", "not_found"} and stop_on_error:
                break
        except Exception as exc:
            error = {"index": index, "step": step, "error": str(exc), "status": "error"}
            transcript.append(error)
            if stop_on_error:
                break
    final = describe_screen(use_ocr=True)
    payload = {"initial_screenshot": initial["screenshot"], "final_screenshot": final["screenshot"], "steps": transcript}
    log_event("visual_steps_run", payload)
    return payload

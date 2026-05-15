from __future__ import annotations

from computer.environment_state import capture_environment_state
from computer.state_diff import verify_action
from computer.uia_executor import invoke_element, type_into_element
from computer.vision import first_text_center
try:
    from computer.visual_executor import click_text_and_verify
except Exception:  # pragma: no cover - optional GUI dependency fallback
    def click_text_and_verify(text: str, verify_text: str | None = None):
        return {"ok": False, "engine": "ocr", "action": "click", "reason": "visual executor unavailable", "text": text}
from security.app_permissions import check_app_permission
from tools.browser_playwright import click_by_role, fill_by_label
from computer.interface_tree_provider import FALLBACK_ORDER


def perform_ui_action(
    target_app: str,
    action: str,
    selector: dict | str,
    text: str | None = None,
    *,
    confirmed: bool = False,
    expected_change: dict | None = None,
    page=None,
    uia_tree: dict | None = None,
) -> dict:
    permission = check_app_permission(target_app, action, selector=selector, text=text, confirmed=confirmed)
    if not permission.get("allowed"):
        return {"ok": False, "stage": "permission", "permission": permission}

    before = capture_environment_state(include_screen=False, include_uia=False)
    attempts = []
    selected = selector if isinstance(selector, dict) else {"name": selector}
    engine_order = list(selected.get("fallback_order") or FALLBACK_ORDER)

    if target_app.lower() in {"chrome.exe", "msedge.exe", "browser"}:
        if action in {"click", "invoke"} and selected.get("role") and selected.get("name"):
            attempts.append(click_by_role(selected["role"], selected["name"], page=page))
        if action in {"fill", "type"} and selected.get("label") and text is not None:
            attempts.append(fill_by_label(selected["label"], text, page=page))

    if action in {"click", "invoke"}:
        attempts.append(invoke_element(name=selected.get("name"), control_type=selected.get("control_type"), tree=uia_tree))
    if action in {"type", "fill"} and text is not None:
        attempts.append(type_into_element(text, name=selected.get("name") or selected.get("label"), control_type=selected.get("control_type"), tree=uia_tree))

    if action in {"click", "invoke"} and selected.get("name"):
        location = first_text_center(selected["name"])
        if location.get("found"):
            attempts.append(click_text_and_verify(selected["name"], expected_change.get("ocr_text") if expected_change else None))
        else:
            attempts.append({"ok": False, "engine": "ocr", "action": "click", "reason": location.get("reason")})

    success = next((row for row in attempts if row.get("ok")), None)
    after = capture_environment_state(include_screen=False, include_uia=False)
    verification = verify_action(before, after, expected_change)
    return {
        "ok": bool(success) and (verification.get("verified") or expected_change is None),
        "engine": success.get("engine") if success else None,
        "engine_order": engine_order,
        "ocr_policy": "OCR is a fallback after DOM/accessibility/UIA/app adapters/shortcuts.",
        "attempts": attempts,
        "verification": verification,
        "permission": permission,
    }

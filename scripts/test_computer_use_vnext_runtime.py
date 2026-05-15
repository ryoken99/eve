from __future__ import annotations

from runtime_validation_lib import append_runtime_jsonl, check, finalize, powershell

from computer.action_router import perform_ui_action
from computer.environment_state import capture_environment_state
from computer.uia_observer import dump_active_window_tree, find_element
from tools.browser_playwright import browser_dom_snapshot, click_by_role, fill_by_label, playwright_available


def main() -> dict:
    logs = []
    dom = browser_dom_snapshot()
    logs.append({"engine": "playwright", "action": "browser_dom_snapshot", "result": dom})
    fake_tree = {"name": "Root", "control_type": "Window", "children": [{"name": "Editor", "control_type": "Edit", "element_id": "edit"}, {"name": "Save", "control_type": "Button", "element_id": "save"}]}
    uia_tree = dump_active_window_tree(max_depth=2)
    found_button = find_element(name="Save", control_type="Button", tree=fake_tree)
    typed = perform_ui_action("notepad.exe", "type", {"name": "Editor", "control_type": "Edit"}, text="hello", uia_tree=fake_tree)
    sensitive = perform_ui_action("chrome.exe", "click", {"role": "button", "name": "submit payment"}, page=None)
    ocr_fallback = perform_ui_action("notepad.exe", "click", {"name": "definitely_missing_runtime_text"}, expected_change={"ocr_text": "missing"}, uia_tree=fake_tree)
    before = capture_environment_state(include_screen=False, include_uia=True, include_browser=True)
    append_runtime_jsonl("computer_use", {"dom": dom, "uia": uia_tree, "typed": typed, "sensitive": sensitive, "ocr_fallback": ocr_fallback, "before": before})
    checks = [
        check("Playwright module available for DOM route", playwright_available(), dom, critical=True),
        check("DOM snapshot reports Playwright engine before OCR", dom.get("engine") == "playwright", dom, critical=True),
        check("click_by_role without page fails without using OCR", not click_by_role("button", "Save")["ok"], click_by_role("button", "Save"), critical=True),
        check("fill_by_label without page fails without using OCR", not fill_by_label("Email", "x")["ok"], fill_by_label("Email", "x")),
        check("UIA tree can be requested", "engine" in uia_tree and uia_tree.get("engine") == "uia", uia_tree, critical=True),
        check("UIA find_element works by name/control_type", found_button["found"], found_button, critical=True),
        check("action router types via UIA before OCR", typed.get("ok") and typed.get("engine") == "uia", typed, critical=True),
        check("sensitive browser action blocks without confirmation", not sensitive.get("ok") and sensitive.get("stage") == "permission", sensitive, critical=True),
        check("OCR fallback is attempted only after structured route fails", any(row.get("engine") == "ocr" for row in ocr_fallback.get("attempts", [])), ocr_fallback),
    ]
    return finalize("point_15_computer_use_runtime", "Point 15 Computer Use VNext Runtime", "point_15_computer_use_runtime.md", checks)


if __name__ == "__main__":
    main()

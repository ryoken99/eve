from __future__ import annotations

try:
    import pyautogui
except Exception:  # pragma: no cover - optional GUI dependency fallback
    pyautogui = None

from computer.emergency_stop import assert_not_locked
from computer.screen_capture import take_screenshot
from computer.ui_action_log import log_ui_action


if pyautogui is not None:
    pyautogui.FAILSAFE = True


def type_text(text: str, interval: float = 0.01) -> dict:
    assert_not_locked()
    before = take_screenshot("before_type_text", scope="all")
    if pyautogui is not None:
        pyautogui.write(text, interval=interval)
    after = take_screenshot("after_type_text", scope="all")
    payload = {"chars": len(text), "before": str(before), "after": str(after), "gui_available": pyautogui is not None}
    log_ui_action("type_text", payload)
    return payload


def press_key(key: str) -> dict:
    assert_not_locked()
    before = take_screenshot("before_press_key", scope="all")
    if pyautogui is not None:
        pyautogui.press(key)
    after = take_screenshot("after_press_key", scope="all")
    payload = {"key": key, "before": str(before), "after": str(after), "gui_available": pyautogui is not None}
    log_ui_action("press_key", payload)
    return payload


def hotkey(*keys: str) -> dict:
    assert_not_locked()
    before = take_screenshot("before_hotkey", scope="all")
    if pyautogui is not None:
        pyautogui.hotkey(*keys)
    after = take_screenshot("after_hotkey", scope="all")
    payload = {"keys": list(keys), "before": str(before), "after": str(after), "gui_available": pyautogui is not None}
    log_ui_action("hotkey", payload)
    return payload

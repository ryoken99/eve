from __future__ import annotations

import pyautogui

from computer.emergency_stop import assert_not_locked
from computer.screen_capture import take_screenshot
from computer.ui_action_log import log_ui_action


pyautogui.FAILSAFE = True


def mouse_position() -> dict:
    x, y = pyautogui.position()
    return {"x": x, "y": y}


def move_mouse(x: int, y: int) -> dict:
    assert_not_locked()
    before = take_screenshot("before_move_mouse")
    pyautogui.moveTo(x, y, duration=0.15)
    after = take_screenshot("after_move_mouse")
    payload = {"x": x, "y": y, "before": str(before), "after": str(after)}
    log_ui_action("move_mouse", payload)
    return payload


def click(x: int, y: int, button: str = "left") -> dict:
    assert_not_locked()
    before = take_screenshot("before_click")
    pyautogui.click(x=x, y=y, button=button)
    after = take_screenshot("after_click")
    payload = {"x": x, "y": y, "button": button, "before": str(before), "after": str(after)}
    log_ui_action("click", payload)
    return payload


def double_click(x: int, y: int) -> dict:
    assert_not_locked()
    before = take_screenshot("before_double_click")
    pyautogui.doubleClick(x=x, y=y)
    after = take_screenshot("after_double_click")
    payload = {"x": x, "y": y, "before": str(before), "after": str(after)}
    log_ui_action("double_click", payload)
    return payload


def scroll(amount: int) -> dict:
    assert_not_locked()
    before = take_screenshot("before_scroll")
    pyautogui.scroll(amount)
    after = take_screenshot("after_scroll")
    payload = {"amount": amount, "before": str(before), "after": str(after)}
    log_ui_action("scroll", payload)
    return payload

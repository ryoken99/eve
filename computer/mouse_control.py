from __future__ import annotations

import pyautogui

from computer.emergency_stop import assert_not_locked
from computer.monitors import monitor_from_point, virtual_bounds
from computer.screen_capture import take_screenshot
from computer.ui_action_log import log_ui_action


pyautogui.FAILSAFE = True


def mouse_position() -> dict:
    x, y = pyautogui.position()
    return {"x": x, "y": y, "monitor": monitor_from_point(x, y), "virtual_bounds": virtual_bounds()}


def _validate_point(x: int, y: int) -> None:
    bounds = virtual_bounds()
    if not (bounds["left"] <= x < bounds["right"] and bounds["top"] <= y < bounds["bottom"]):
        raise ValueError(f"Coordenadas fora do desktop virtual: x={x}, y={y}, bounds={bounds}")


def move_mouse(x: int, y: int) -> dict:
    assert_not_locked()
    _validate_point(x, y)
    before = take_screenshot("before_move_mouse", scope="all")
    pyautogui.moveTo(x, y, duration=0.15)
    after = take_screenshot("after_move_mouse", scope="all")
    payload = {"x": x, "y": y, "monitor": monitor_from_point(x, y), "before": str(before), "after": str(after)}
    log_ui_action("move_mouse", payload)
    return payload


def click(x: int, y: int, button: str = "left") -> dict:
    assert_not_locked()
    _validate_point(x, y)
    before = take_screenshot("before_click", scope="all")
    pyautogui.click(x=x, y=y, button=button)
    after = take_screenshot("after_click", scope="all")
    payload = {"x": x, "y": y, "button": button, "monitor": monitor_from_point(x, y), "before": str(before), "after": str(after)}
    log_ui_action("click", payload)
    return payload


def double_click(x: int, y: int) -> dict:
    assert_not_locked()
    _validate_point(x, y)
    before = take_screenshot("before_double_click", scope="all")
    pyautogui.doubleClick(x=x, y=y)
    after = take_screenshot("after_double_click", scope="all")
    payload = {"x": x, "y": y, "monitor": monitor_from_point(x, y), "before": str(before), "after": str(after)}
    log_ui_action("double_click", payload)
    return payload


def scroll(amount: int) -> dict:
    assert_not_locked()
    before = take_screenshot("before_scroll", scope="all")
    pyautogui.scroll(amount)
    after = take_screenshot("after_scroll", scope="all")
    payload = {"amount": amount, "before": str(before), "after": str(after)}
    log_ui_action("scroll", payload)
    return payload

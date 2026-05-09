from __future__ import annotations

from computer.keyboard_control import hotkey, press_key, type_text
from computer.mouse_control import scroll
from computer.vision import describe_screen
from computer.visual_executor import click_text_and_verify
from tools.web_research import fetch_url


def browser_snapshot() -> dict:
    return describe_screen(use_ocr=True, scope="all")


def browser_back() -> dict:
    return hotkey("alt", "left")


def browser_click_text(text: str, verify_text: str | None = None) -> dict:
    return click_text_and_verify(text, verify_text)


def browser_type_text(text: str, *, submit: bool = False) -> dict:
    result = type_text(text)
    if submit:
        result["submit"] = press_key("enter")
    return result


def browser_scroll(amount: int = -5) -> dict:
    return scroll(amount)


def browser_fetch_url(url: str) -> dict:
    page = fetch_url(url)
    page.pop("html", None)
    return page


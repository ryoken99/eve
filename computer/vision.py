from __future__ import annotations

from computer.active_window import get_active_window_title
from computer.ocr import ocr_image, ocr_screen
from computer.screen_capture import screen_size, take_screenshot


def describe_screen(use_ocr: bool = True) -> dict:
    path = take_screenshot()
    width, height = screen_size()
    result = {
        "screenshot": str(path),
        "screen_size": {"width": width, "height": height},
        "active_window": get_active_window_title(),
    }
    if use_ocr:
        result["ocr_text"] = ocr_image(path)
    return result


def find_text_on_screen(text: str) -> dict:
    observed = ocr_screen()
    haystack = observed["text"].lower()
    needle = text.lower()
    return {
        "found": needle in haystack,
        "query": text,
        "screenshot": observed["screenshot"],
        "text_excerpt": observed["text"][:2000],
    }

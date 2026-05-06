from __future__ import annotations

from computer.active_window import get_active_window_title
from computer.monitors import list_monitors, virtual_bounds
from computer.ocr import ocr_desktop_data, ocr_image
from computer.screen_capture import capture_desktop, capture_monitor, screen_size, take_screenshot


def describe_screen(use_ocr: bool = True, *, scope: str = "all") -> dict:
    if scope == "all":
        capture = capture_desktop()
        path = capture["screenshot"]
        bounds = capture["bounds"]
    else:
        path = str(take_screenshot())
        width, height = screen_size()
        bounds = {"left": 0, "top": 0, "width": width, "height": height}
    result = {
        "screenshot": str(path),
        "bounds": bounds,
        "monitors": list_monitors(),
        "active_window": get_active_window_title(),
    }
    if use_ocr:
        result["ocr_text"] = ocr_image(path)
    return result


def find_text_on_screen(text: str) -> dict:
    observed = ocr_desktop_data()
    needle = text.lower()
    matches = [entry for entry in observed["entries"] if needle in entry["text"].lower()]
    return {
        "found": bool(matches),
        "query": text,
        "screenshot": observed["screenshot"],
        "bounds": observed["bounds"],
        "matches": matches[:20],
        "match_count": len(matches),
        "ocr_sample": observed["entries"][:40],
    }


def first_text_center(text: str) -> dict:
    result = find_text_on_screen(text)
    if not result["matches"]:
        return {"found": False, "query": text, "reason": "texto nao localizado por OCR", "ocr_sample": result["ocr_sample"]}
    box = result["matches"][0]["global_box"]
    return {"found": True, "query": text, "x": box["center_x"], "y": box["center_y"], "match": result["matches"][0]}


def monitor_report() -> dict:
    return {"virtual_bounds": virtual_bounds(), "monitors": list_monitors()}


def screenshot_monitor(index: int) -> dict:
    return capture_monitor(index)

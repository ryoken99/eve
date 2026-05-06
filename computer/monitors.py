from __future__ import annotations

import ctypes
from ctypes import wintypes


def list_monitors() -> list[dict]:
    monitors: list[dict] = []

    user32 = ctypes.windll.user32

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    monitor_enum_proc = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(RECT),
        ctypes.c_double,
    )

    def callback(hmonitor, _hdc, rect, _data):
        left, top, right, bottom = rect.contents.left, rect.contents.top, rect.contents.right, rect.contents.bottom
        monitors.append(
            {
                "index": len(monitors),
                "handle": int(hmonitor),
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom,
                "width": right - left,
                "height": bottom - top,
            }
        )
        return 1

    user32.EnumDisplayMonitors(0, 0, monitor_enum_proc(callback), 0)
    return monitors


def virtual_bounds() -> dict:
    monitors = list_monitors()
    if not monitors:
        return {"left": 0, "top": 0, "right": 0, "bottom": 0, "width": 0, "height": 0}
    left = min(m["left"] for m in monitors)
    top = min(m["top"] for m in monitors)
    right = max(m["right"] for m in monitors)
    bottom = max(m["bottom"] for m in monitors)
    return {"left": left, "top": top, "right": right, "bottom": bottom, "width": right - left, "height": bottom - top}


def monitor_from_point(x: int, y: int) -> dict | None:
    for monitor in list_monitors():
        if monitor["left"] <= x < monitor["right"] and monitor["top"] <= y < monitor["bottom"]:
            return monitor
    return None


def point_to_image_coords(x: int, y: int, origin: dict) -> dict:
    return {"x": x - origin["left"], "y": y - origin["top"]}


def image_to_global_coords(x: int, y: int, origin: dict) -> dict:
    return {"x": x + origin["left"], "y": y + origin["top"]}

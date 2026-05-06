from __future__ import annotations

import ctypes
import platform


def get_active_window_title() -> str:
    if platform.system().lower() != "windows":
        return "unsupported"
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "unknown"
        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value or "unknown"
    except Exception as exc:
        return f"error: {exc}"

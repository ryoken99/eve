from __future__ import annotations

from app.dashboard import render_dashboard


MENU = [
    ("1", "Dashboard", "/dashboard"),
    ("2", "Estado", "/estado"),
    ("3", "Seguranca", "/seguranca"),
    ("4", "Monitores", "/monitores"),
    ("5", "OCR", "/ocr-status"),
    ("6", "Memoria vetorial", "/vector-index"),
    ("7", "Research tecnologia", "/watch-tech"),
    ("8", "Modo seguro", "/seguranca-safe menu"),
    ("9", "Liberdade total", "/liberdade-total menu"),
]


def render_menu() -> str:
    lines = ["EVE MENU", ""]
    for key, label, command in MENU:
        lines.append(f"{key}. {label}  [{command}]")
    return "\n".join(lines)

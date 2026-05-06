from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image
from pytesseract import TesseractNotFoundError

from computer.monitors import image_to_global_coords, virtual_bounds
from computer.screen_capture import take_screenshot
from computer.ui_action_log import log_ui_action


def ocr_status() -> dict:
    try:
        version = str(pytesseract.get_tesseract_version())
        return {"available": True, "version": version, "error": None}
    except TesseractNotFoundError:
        return {
            "available": False,
            "version": None,
            "error": "tesseract.exe nao esta instalado ou nao esta no PATH",
            "fix": "Instalar Tesseract OCR para Windows e adicionar o executavel ao PATH.",
        }
    except Exception as exc:
        return {"available": False, "version": None, "error": str(exc)}


def ocr_image(path: str | Path) -> str:
    image_path = Path(path)
    try:
        text = pytesseract.image_to_string(Image.open(image_path), lang="eng+por")
    except TesseractNotFoundError:
        text = "OCR indisponivel: tesseract.exe nao esta instalado ou nao esta no PATH"
    except Exception as exc:
        text = f"OCR indisponivel: {exc}"
    log_ui_action("ocr_image", {"path": str(image_path), "chars": len(text)})
    return text.strip()


def ocr_screen() -> dict:
    path = take_screenshot()
    text = ocr_image(path)
    return {"screenshot": str(path), "text": text}


def ocr_image_data(path: str | Path, *, origin: dict | None = None) -> list[dict]:
    image_path = Path(path)
    origin = origin or {"left": 0, "top": 0}
    try:
        data = pytesseract.image_to_data(Image.open(image_path), lang="eng+por", output_type=pytesseract.Output.DICT)
    except TesseractNotFoundError as exc:
        log_ui_action("ocr_image_data_failed", {"path": str(image_path), "error": "tesseract_not_found"})
        return []
    except Exception as exc:
        log_ui_action("ocr_image_data_failed", {"path": str(image_path), "error": str(exc)})
        return []

    entries: list[dict] = []
    for index, text in enumerate(data.get("text", [])):
        clean = (text or "").strip()
        if not clean:
            continue
        left = int(data["left"][index])
        top = int(data["top"][index])
        width = int(data["width"][index])
        height = int(data["height"][index])
        global_pos = image_to_global_coords(left, top, origin)
        entries.append(
            {
                "text": clean,
                "confidence": float(data["conf"][index]) if str(data["conf"][index]).replace(".", "", 1).lstrip("-").isdigit() else -1,
                "image_box": {"left": left, "top": top, "width": width, "height": height},
                "global_box": {
                    "left": global_pos["x"],
                    "top": global_pos["y"],
                    "width": width,
                    "height": height,
                    "center_x": global_pos["x"] + width // 2,
                    "center_y": global_pos["y"] + height // 2,
                },
            }
        )
    log_ui_action("ocr_image_data", {"path": str(image_path), "entries": len(entries)})
    return entries


def ocr_desktop_data() -> dict:
    path = take_screenshot(scope="all")
    bounds = virtual_bounds()
    entries = ocr_image_data(path, origin=bounds)
    return {"screenshot": str(path), "bounds": bounds, "entries": entries}

from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image

from computer.screen_capture import take_screenshot
from computer.ui_action_log import log_ui_action


def ocr_image(path: str | Path) -> str:
    image_path = Path(path)
    try:
        text = pytesseract.image_to_string(Image.open(image_path), lang="eng+por")
    except Exception as exc:
        text = f"OCR indisponivel: {exc}"
    log_ui_action("ocr_image", {"path": str(image_path), "chars": len(text)})
    return text.strip()


def ocr_screen() -> dict:
    path = take_screenshot()
    text = ocr_image(path)
    return {"screenshot": str(path), "text": text}

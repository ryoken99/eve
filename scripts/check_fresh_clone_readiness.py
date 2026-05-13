from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_IMPORTS = [
    "PIL",
    "pyautogui",
    "pynput",
    "pytesseract",
    "sklearn",
    "cv2",
    "uiautomation",
    "playwright",
    "sentence_transformers",
]


PORTABLE_FILES = [
    ROOT / "eve.ps1",
    ROOT / "requirements.txt",
    *sorted((ROOT / "scripts").glob("*.cmd")),
    *sorted((ROOT / "scripts").glob("*.ps1")),
    ROOT / "core" / "paths.py",
    ROOT / "config" / "browser.json",
]


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _scan_hardcoded_launch_paths() -> list[str]:
    findings: list[str] = []
    needles = ["D:\\Eve", "D:/Eve", "E:\\eve", "E:/eve", "E:\\Eve", "D:\\eve"]
    for path in PORTABLE_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in needles:
            if needle in text:
                findings.append(f"{path.relative_to(ROOT)} contains {needle}")
    return findings


def main() -> int:
    missing_modules = [name for name in REQUIRED_IMPORTS if not _has_module(name)]
    hardcoded_paths = _scan_hardcoded_launch_paths()
    playwright_ready = _has_module("playwright") and (shutil.which("python") is not None)
    tesseract_ready = shutil.which("tesseract") is not None

    payload = {
        "root": str(ROOT),
        "python": sys.executable,
        "ok": not missing_modules and not hardcoded_paths,
        "missing_python_modules": missing_modules,
        "hardcoded_launch_paths": hardcoded_paths,
        "playwright_package_present": playwright_ready,
        "tesseract_executable_on_path": tesseract_ready,
        "notes": [
            "Run: powershell -ExecutionPolicy Bypass -File scripts\\bootstrap_windows.ps1 -CreateVenv -InstallPlaywright -ConfigureLocalAccount",
            "Tesseract OCR is optional for DOM/UIA paths but required for OCR fallback.",
            "Per-machine state, secrets, Codex login and scheduled tasks are intentionally not cloned.",
        ],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

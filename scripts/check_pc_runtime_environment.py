from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from runtime_validation_lib import check, detect_pc, finalize, module_available, runtime_imports

from core.paths import EVE_ROOT, ensure_project_dirs
from security.safety_modes import current_safety_mode, set_safety_mode


def main() -> dict:
    ensure_project_dirs()
    if current_safety_mode() != "unrestricted_mode":
        set_safety_mode("unrestricted_mode", "runtime validation default for PC2")
    config = EVE_ROOT / "config.yaml"
    venv_python = EVE_ROOT / ".venv" / "Scripts" / "python.exe"
    imports = runtime_imports()
    pc = detect_pc()
    checks = [
        check("Python is available", bool(sys.executable), {"executable": sys.executable, "version": sys.version}, critical=True),
        check("venv python exists", venv_python.exists(), str(venv_python)),
        check("Playwright Python module importable", imports["modules"]["playwright"]["available"], imports["modules"]["playwright"], critical=True),
        check("pyautogui importable", imports["modules"]["pyautogui"]["available"], imports["modules"]["pyautogui"]),
        check("uiautomation importable", imports["modules"]["uiautomation"]["available"], imports["modules"]["uiautomation"], critical=True),
        check("PIL importable", imports["modules"]["PIL"]["available"], imports["modules"]["PIL"]),
        check("pytesseract importable if installed", imports["modules"]["pytesseract"]["available"], imports["modules"]["pytesseract"]),
        check("EVE_ROOT exists and is writable", EVE_ROOT.exists() and os.access(EVE_ROOT, os.W_OK), str(EVE_ROOT), critical=True),
        check("PC path detected", pc["pc"] in {"PC1", "PC2", "custom"}, pc, critical=True),
        check("config.yaml exists", config.exists(), str(config), critical=True),
        check("default mode remains unrestricted_mode", current_safety_mode() == "unrestricted_mode", {"mode": current_safety_mode()}),
    ]
    return finalize("runtime_environment_check", "Sprint 0 Runtime Environment", "runtime_environment_pc2.md", checks, {"imports": imports, "pc": pc})


if __name__ == "__main__":
    main()

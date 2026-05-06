from __future__ import annotations

from security.admin_gate import admin_allowed, request_admin
from tools.terminal import run_command
import subprocess
from pathlib import Path
from core.paths import EVE_ROOT


def run_admin_command(command: str, reason: str, *, approved: bool = False) -> dict:
    if not approved:
        return request_admin(reason, command)
    if not admin_allowed(True):
        return {"allowed": False, "reason": "admin nao permitido"}
    return run_command(command, approved=True)


def launch_elevated_powershell(command: str) -> dict:
    script = EVE_ROOT / "backups" / "tmp" / "eve_admin_command.ps1"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(command, encoding="utf-8")
    ps_command = f"Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"{script}\"'"
    completed = subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], capture_output=True, text=True, timeout=60)
    return {"script": str(script), "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.paths import EVE_ROOT
from security.audit_log import log_event


def create_daily_task(name: str, time_hhmm: str, command: str | None = None) -> dict:
    command = command or f'"{sys.executable}" "{EVE_ROOT / "scripts" / "eve_maintenance.py"}"'
    task_name = f"Eve_{name}"
    args = [
        "schtasks",
        "/Create",
        "/SC",
        "DAILY",
        "/TN",
        task_name,
        "/TR",
        command,
        "/ST",
        time_hhmm,
        "/F",
    ]
    completed = subprocess.run(args, capture_output=True, text=True, timeout=60)
    result = {"task": task_name, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    log_event("windows_task_create", result)
    return result


def list_eve_tasks() -> dict:
    completed = subprocess.run(["schtasks", "/Query", "/FO", "LIST"], capture_output=True, text=True, timeout=60)
    lines = [line for line in completed.stdout.splitlines() if "Eve_" in line]
    return {"returncode": completed.returncode, "tasks": lines, "stderr": completed.stderr}

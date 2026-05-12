from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.paths import EVE_ROOT, LOGS_DIR
from security.audit_log import log_event


TASK_WRAPPER_DIR = LOGS_DIR / "scheduled_tasks" / "wrappers"


def write_task_wrapper(name: str, command: str) -> Path:
    TASK_WRAPPER_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(char if char.isalnum() or char in "-_" else "_" for char in name)[:120] or "task"
    path = TASK_WRAPPER_DIR / f"{safe_name}.cmd"
    path.write_text(f"@echo off\r\ncd /d {EVE_ROOT}\r\n{command}\r\n", encoding="utf-8")
    return path


def build_task_wrapper_command(wrapper_path: str | Path) -> str:
    return f'cmd.exe /c ""{Path(wrapper_path)}""'


def create_once_task(
    name: str,
    time_hhmm: str,
    date_ddmmyyyy: str,
    command: str,
    *,
    interactive: bool = False,
    highest: bool = False,
) -> dict:
    task_name = f"Eve_{name}"
    wrapper_path = write_task_wrapper(task_name, command)
    wrapped_command = build_task_wrapper_command(wrapper_path)
    args = [
        "schtasks",
        "/Create",
        "/SC",
        "ONCE",
        "/TN",
        task_name,
        "/TR",
        wrapped_command,
        "/ST",
        time_hhmm,
        "/SD",
        date_ddmmyyyy,
        "/F",
    ]
    if interactive:
        args.append("/IT")
    if highest:
        args.extend(["/RL", "HIGHEST"])
    completed = subprocess.run(args, capture_output=True, text=True, timeout=60)
    result = {
        "task": task_name,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "wrapper": str(wrapper_path),
        "wrapped_command": wrapped_command,
    }
    log_event("windows_task_create_once", result)
    return result


def create_daily_task(name: str, time_hhmm: str, command: str | None = None, *, highest: bool = False) -> dict:
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
    if highest:
        args.extend(["/RL", "HIGHEST"])
    completed = subprocess.run(args, capture_output=True, text=True, timeout=60)
    result = {"task": task_name, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "highest": highest, "args": args}
    log_event("windows_task_create", result)
    return result


def list_eve_tasks() -> dict:
    completed = subprocess.run(["schtasks", "/Query", "/FO", "LIST"], capture_output=True, text=True, timeout=60)
    lines = [line for line in completed.stdout.splitlines() if "Eve_" in line]
    return {"returncode": completed.returncode, "tasks": lines, "stderr": completed.stderr}

from __future__ import annotations

import ctypes
import json
import platform
from security.admin_gate import admin_allowed, request_admin
from security.safety_modes import current_safety_mode, current_safety_profile
from tools.terminal import run_command
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from core.paths import EVE_ROOT, LOGS_DIR, ensure_project_dirs
from security.admin_session import validate_admin_session


def is_admin_process() -> bool:
    if platform.system().lower() != "windows":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def admin_log_path() -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "admin_actions" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def log_admin_action(event: str, payload: dict) -> Path:
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event": event,
        **payload,
    }
    path = admin_log_path()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def admin_status() -> dict:
    profile = current_safety_profile()
    return {
        "is_admin_process": is_admin_process(),
        "safety_mode": current_safety_mode(),
        "admin_requires_approval": profile.get("admin_requires_approval", True),
        "can_launch_elevated_powershell": True,
        "elevated_startup_supported": True,
        "audit_log": str(admin_log_path()),
    }


def run_admin_command(command: str, reason: str, *, approved: bool = False, session_id: str | None = None, dry_run: bool = False) -> dict:
    log_admin_action("admin_command_requested", {"reason": reason, "approved": approved, "command": command, "session_id": session_id, "dry_run": dry_run})
    if dry_run:
        validation = validate_admin_session(session_id, command) if session_id else {"allowed": True, "reason": "dry run without session"}
        result = {"allowed": bool(validation.get("allowed")), "status": "dry_run", "command": command, "reason": reason, "session_validation": validation}
        log_admin_action("admin_command_dry_run", result)
        return result
    if not approved:
        return request_admin(reason, command)
    validation = validate_admin_session(session_id, command)
    if not validation.get("allowed"):
        log_admin_action("admin_command_blocked_by_session", {"reason": reason, "command": command, "session_validation": validation})
        return {"allowed": False, "reason": validation.get("reason"), "session_validation": validation}
    if not admin_allowed(True):
        return {"allowed": False, "reason": "admin nao permitido"}
    if not is_admin_process():
        elevated = launch_elevated_powershell(command, reason=reason)
        log_admin_action("admin_command_elevation_requested", {"reason": reason, "command": command, "result": elevated})
        return {"allowed": True, "status": "elevation_requested", "admin": admin_status(), "elevated": elevated}
    result = run_command(command, approved=True)
    log_admin_action("admin_command_executed_in_admin_process", {"reason": reason, "command": command, "result": result})
    return {"allowed": True, "status": "executed", "admin": admin_status(), "result": result}


def launch_elevated_powershell(command: str, *, reason: str = "Eve elevated command", dry_run: bool = False) -> dict:
    script = EVE_ROOT / "backups" / "tmp" / "eve_admin_command.ps1"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                f"# Reason: {reason}",
                command,
                "",
            ]
        ),
        encoding="utf-8",
    )
    ps_command = f"Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"{script}\"'"
    payload = {"script": str(script), "powershell_command": ps_command, "reason": reason, "dry_run": dry_run}
    log_admin_action("elevated_powershell_prepared", payload)
    if dry_run:
        return {**payload, "returncode": None, "stdout": "", "stderr": "", "status": "dry_run"}
    completed = subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], capture_output=True, text=True, timeout=60)
    result = {**payload, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "status": "launched"}
    log_admin_action("elevated_powershell_launched", result)
    return result

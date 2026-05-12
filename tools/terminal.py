from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from core.paths import LOGS_DIR, WORKSPACE_DIR, ensure_project_dirs
from memory.daily_transcripts import append_transcript
from memory.errors.error_memory import record_error
from security.approval import request_approval
from security.audit_log import log_event
from security.permission_manager import check_command


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def terminal_log_path() -> Path:
    ensure_project_dirs()
    return LOGS_DIR / "terminal" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"


def run_command(command: str, *, cwd: str | None = None, approved: bool = False, timeout: int = 60) -> dict:
    decision = check_command(command, approved=approved)
    if not decision.allowed:
        approval = request_approval(
            "run_terminal_command",
            decision.reason,
            "medium" if decision.requires_approval else "low",
            {"command": command, "cwd": cwd or str(WORKSPACE_DIR)},
        )
        result = {
            "timestamp": now_iso(),
            "command": command,
            "cwd": cwd or str(WORKSPACE_DIR),
            "allowed": False,
            "requires_approval": decision.requires_approval,
            "reason": decision.reason,
            "approval": approval,
        }
        _append_log(result)
        log_event("terminal_blocked", result)
        return result

    workdir = Path(cwd).resolve() if cwd else WORKSPACE_DIR.resolve()
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:
        record_error("terminal", command, type(exc).__name__, str(exc), resolved=False)
        result = {
            "timestamp": now_iso(),
            "command": command,
            "cwd": str(workdir),
            "allowed": True,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }
        _append_log(result)
        log_event("terminal_error", result)
        return result
    result = {
        "timestamp": now_iso(),
        "command": command,
        "cwd": str(workdir),
        "allowed": True,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-8000:],
    }
    _append_log(result)
    log_event("terminal_executed", {k: result[k] for k in ("command", "cwd", "returncode")})
    if proc.returncode != 0 or proc.stderr.strip():
        record_error("terminal", command, f"exit_{proc.returncode}", proc.stderr or proc.stdout, resolved=False)
    return result


def _append_log(entry: dict) -> None:
    with terminal_log_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    append_transcript("tools", "terminal_command", entry)

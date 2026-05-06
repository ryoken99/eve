from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from core.paths import LOGS_DIR, WORKSPACE_DIR, ensure_project_dirs
from security.permission_manager import check_command


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def terminal_log_path() -> Path:
    ensure_project_dirs()
    return LOGS_DIR / "terminal" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"


def run_command(command: str, *, cwd: str | None = None, approved: bool = False, timeout: int = 60) -> dict:
    decision = check_command(command, approved=approved)
    if not decision.allowed:
        result = {
            "timestamp": now_iso(),
            "command": command,
            "cwd": cwd or str(WORKSPACE_DIR),
            "allowed": False,
            "requires_approval": decision.requires_approval,
            "reason": decision.reason,
        }
        _append_log(result)
        return result

    workdir = Path(cwd).resolve() if cwd else WORKSPACE_DIR.resolve()
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=str(workdir),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
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
    return result


def _append_log(entry: dict) -> None:
    with terminal_log_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

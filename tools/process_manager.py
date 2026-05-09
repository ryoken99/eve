from __future__ import annotations

import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import LOGS_DIR, STATE_DIR, ensure_project_dirs
from security.audit_log import log_event


PROCESS_PATH = STATE_DIR / "processes.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load() -> dict[str, Any]:
    ensure_project_dirs()
    if not PROCESS_PATH.exists():
        return {}
    try:
        return json.loads(PROCESS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(processes: dict[str, Any]) -> Path:
    PROCESS_PATH.write_text(json.dumps(processes, indent=2, ensure_ascii=False), encoding="utf-8")
    return PROCESS_PATH


def start_process(command: str, *, cwd: str | None = None) -> dict[str, Any]:
    ensure_project_dirs()
    process_id = f"proc_{uuid.uuid4().hex[:10]}"
    log_dir = LOGS_DIR / "processes"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / f"{process_id}.out.log"
    stderr_path = log_dir / f"{process_id}.err.log"
    stdout = stdout_path.open("w", encoding="utf-8")
    stderr = stderr_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=cwd,
        stdout=stdout,
        stderr=stderr,
        text=True,
    )
    # We intentionally do not keep the Popen object in memory; the persisted PID
    # is managed through poll/stop. Mark as detached to avoid destructor warnings.
    proc._child_created = False  # type: ignore[attr-defined]
    stdout.close()
    stderr.close()
    processes = _load()
    entry = {
        "id": process_id,
        "pid": proc.pid,
        "command": command,
        "cwd": cwd,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "started_at": now_iso(),
        "status": "running",
    }
    processes[process_id] = entry
    _save(processes)
    log_event("process_started", entry)
    return entry


def list_processes() -> list[dict[str, Any]]:
    return list(_load().values())


def poll_process(process_id: str) -> dict[str, Any]:
    processes = _load()
    entry = processes.get(process_id)
    if not entry:
        raise FileNotFoundError(f"Processo nao encontrado: {process_id}")
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", f"(Get-Process -Id {int(entry['pid'])} -ErrorAction SilentlyContinue) -ne $null"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    running = "True" in completed.stdout
    entry["status"] = "running" if running else "exited"
    entry["polled_at"] = now_iso()
    _save(processes)
    return entry


def stop_process(process_id: str) -> dict[str, Any]:
    processes = _load()
    entry = processes.get(process_id)
    if not entry:
        raise FileNotFoundError(f"Processo nao encontrado: {process_id}")
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", f"Stop-Process -Id {int(entry['pid'])} -Force -ErrorAction SilentlyContinue"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    entry["status"] = "stopped"
    entry["stopped_at"] = now_iso()
    entry["stop_result"] = {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    _save(processes)
    log_event("process_stopped", entry)
    return entry

from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from computer.active_window import get_active_window_title
from core.paths import EVE_ROOT, STATE_DIR, ensure_project_dirs


STATE_PATH = STATE_DIR / "current_world_state.json"
STATUS_PATH = STATE_DIR / "eve_status.json"


def _load_status() -> dict:
    if not STATUS_PATH.exists():
        return {}
    try:
        return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _top_process_names(limit: int = 12) -> list[str]:
    if platform.system().lower() != "windows":
        return []
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Process | Sort-Object CPU -Descending | Select-Object -First 12 -ExpandProperty ProcessName"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if completed.returncode != 0:
            return []
        names = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        return names[:limit]
    except Exception:
        return []


def collect_awareness() -> dict:
    ensure_project_dirs()
    status = _load_status()
    now = datetime.now(ZoneInfo("Europe/Lisbon"))
    state = {
        "timestamp": now.isoformat(timespec="seconds"),
        "timezone": "Europe/Lisbon",
        "system": {
            "os": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "eve": {
            "root": str(EVE_ROOT),
            "cwd": os.getcwd(),
            "mode": status.get("mode", "safe_mode"),
            "active_project": status.get("active_project", "Eve"),
            "active_task": status.get("active_task", "idle"),
        },
        "desktop": {
            "active_window": get_active_window_title(),
            "top_processes": _top_process_names(),
        },
        "user": {
            "name": status.get("user", "Sandro"),
        },
    }
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return state


def describe_awareness() -> str:
    state = collect_awareness()
    system = state["system"]
    eve = state["eve"]
    desktop = state["desktop"]
    return "\n".join(
        [
            f"Hora: {state['timestamp']} ({state['timezone']})",
            f"Sistema: {system['os']} {system['release']} {system['machine']}",
            f"Modo: {eve['mode']}",
            f"Projeto ativo: {eve['active_project']}",
            f"Tarefa ativa: {eve['active_task']}",
            f"Pasta Eve: {eve['root']}",
            f"Janela ativa: {desktop['active_window']}",
            "Processos principais: " + (", ".join(desktop["top_processes"]) if desktop["top_processes"] else "indisponivel"),
        ]
    )

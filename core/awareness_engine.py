from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path

from computer.active_window import get_active_window_title
from computer.computer_use_observation import ComputerUseObservation
from computer.interface_tree_provider import provider_priority
from core.admin_capability import admin_capability_status
from core.gateway_manager import gateway_state
from core.paths import EVE_ROOT, STATE_DIR, ensure_project_dirs
from core.time_utils import now_lisbon
from core.world_state_schema import WorldState


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
    now = now_lisbon()
    daemon_heartbeat = STATE_DIR / "daemon_heartbeat.json"
    autonomy_status = {}
    if daemon_heartbeat.exists():
        try:
            autonomy_status = json.loads(daemon_heartbeat.read_text(encoding="utf-8"))
        except Exception:
            autonomy_status = {"heartbeat": "unreadable"}
    computer_observation = ComputerUseObservation(
        app={"active_window": get_active_window_title()},
        tree={"provider_priority": provider_priority()},
        preferred_engine="browser_dom",
        fallback_order=provider_priority(),
        notes=["OCR is a fallback, not the primary perception layer."],
    )
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
            "mode": status.get("mode", "unrestricted_mode"),
            "active_project": status.get("active_project", "Eve"),
            "active_task": status.get("active_task", "idle"),
        },
        "desktop": {
            "active_window": get_active_window_title(),
            "top_processes": _top_process_names(),
        },
        "gateway": gateway_state(),
        "user": {
            "name": status.get("user", "Sandro"),
        },
        "admin": admin_capability_status(),
        "autonomy": {
            "daemon_heartbeat_exists": daemon_heartbeat.exists(),
            "last_heartbeat": autonomy_status.get("timestamp"),
            "cron_errors": autonomy_status.get("cron", {}).get("errors", []) if isinstance(autonomy_status.get("cron"), dict) else [],
        },
        "memory": {
            "layers": ["short_term", "medium_term", "long_term", "semantic_vector"],
            "current_world_state_path": str(STATE_PATH),
        },
        "computer_use_observation": computer_observation.__dict__,
    }
    state["world_state_schema"] = WorldState(
        timestamp=state["timestamp"],
        timezone=state["timezone"],
        active_pc=state["system"]["machine"],
        active_window=state["desktop"]["active_window"],
        active_app=state["desktop"]["active_window"],
        system_status=state["system"],
        autonomy_status=state["autonomy"],
        current_user_context=state["user"],
        computer_use_observation=state["computer_use_observation"],
        admin_status=state["admin"],
        memory_status=state["memory"],
    ).as_dict()
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
            f"Gateway web: porta {state['gateway'].get('port')} listening={state['gateway'].get('listening')} ui={state['gateway'].get('ui_version')} uptime={state['gateway'].get('uptime_seconds')}",
            f"Janela ativa: {desktop['active_window']}",
            "Processos principais: " + (", ".join(desktop["top_processes"]) if desktop["top_processes"] else "indisponivel"),
        ]
    )

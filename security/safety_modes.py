from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import STATE_DIR, ensure_project_dirs
from security.audit_log import log_event


STATUS_PATH = STATE_DIR / "eve_status.json"
DEFAULT_SAFETY_MODE = "unrestricted_mode"

SAFETY_MODES = {
    "safe_mode": {
        "description": "Conversar, memoria e tarefas locais de baixo risco.",
        "action_guard": True,
        "command_guard": True,
        "admin_requires_approval": True,
        "self_modify_requires_approval": True,
        "ui_control": False,
        "emergency_lock_enabled": True,
    },
    "work_mode": {
        "description": "Workspace e terminal seguro, sem controlo total do PC.",
        "action_guard": True,
        "command_guard": True,
        "admin_requires_approval": True,
        "self_modify_requires_approval": True,
        "ui_control": False,
        "emergency_lock_enabled": True,
    },
    "operator_mode": {
        "description": "Controlo visual/rato/teclado com guards sensiveis ligados.",
        "action_guard": True,
        "command_guard": True,
        "admin_requires_approval": True,
        "self_modify_requires_approval": True,
        "ui_control": True,
        "emergency_lock_enabled": True,
    },
    "admin_mode": {
        "description": "Permite admin quando aprovado explicitamente.",
        "action_guard": True,
        "command_guard": True,
        "admin_requires_approval": True,
        "self_modify_requires_approval": True,
        "ui_control": True,
        "emergency_lock_enabled": True,
    },
    "unrestricted_mode": {
        "description": "Liberdade total: admin, comandos perigosos, UI e self-modify sem approval interno.",
        "action_guard": False,
        "command_guard": False,
        "admin_requires_approval": False,
        "self_modify_requires_approval": False,
        "ui_control": True,
        "emergency_lock_enabled": False,
    },
}


def _load_status() -> dict:
    ensure_project_dirs()
    if not STATUS_PATH.exists():
        return {}
    try:
        return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_status(status: dict) -> Path:
    ensure_project_dirs()
    STATUS_PATH.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    return STATUS_PATH


def current_safety_mode() -> str:
    status = _load_status()
    mode = status.get("mode", DEFAULT_SAFETY_MODE)
    return mode if mode in SAFETY_MODES else DEFAULT_SAFETY_MODE


def current_safety_profile() -> dict:
    return SAFETY_MODES[current_safety_mode()]


def set_safety_mode(mode: str, reason: str = "") -> Path:
    if mode not in SAFETY_MODES:
        raise ValueError(f"Modo desconhecido: {mode}. Modos: {', '.join(SAFETY_MODES)}")
    status = _load_status()
    previous = status.get("mode", DEFAULT_SAFETY_MODE)
    profile = SAFETY_MODES[mode]
    status["mode"] = mode
    status["computer_control"] = bool(profile["ui_control"])
    status["admin_mode"] = mode in {"admin_mode", "unrestricted_mode"}
    status["safety"] = {
        "mode": mode,
        "description": profile["description"],
        "action_guard": profile["action_guard"],
        "command_guard": profile["command_guard"],
        "admin_requires_approval": profile["admin_requires_approval"],
        "self_modify_requires_approval": profile["self_modify_requires_approval"],
        "emergency_lock_enabled": profile["emergency_lock_enabled"],
        "changed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "reason": reason,
    }
    path = _save_status(status)
    log_event(
        "safety_mode_changed",
        {"previous": previous, "current": mode, "reason": reason, "profile": status["safety"]},
    )
    return path


def describe_safety() -> str:
    status = _load_status()
    mode = current_safety_mode()
    profile = SAFETY_MODES[mode]
    return "\n".join(
        [
            f"Modo: {mode}",
            f"Descricao: {profile['description']}",
            f"Action guard: {profile['action_guard']}",
            f"Command guard: {profile['command_guard']}",
            f"Admin requer approval: {profile['admin_requires_approval']}",
            f"Self-modify requer approval: {profile['self_modify_requires_approval']}",
            f"UI control: {profile['ui_control']}",
            f"Emergency lock ativo no perfil: {profile['emergency_lock_enabled']}",
            f"Ultima razao: {(status.get('safety') or {}).get('reason', '')}",
        ]
    )

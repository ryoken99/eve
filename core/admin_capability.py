from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from security.admin_session import list_admin_sessions
from tools.admin_executor import admin_status


class AdminState(str, Enum):
    NOT_ADMIN = "not_admin"
    ADMIN_AVAILABLE = "admin_available"
    ELEVATED_PROCESS_AVAILABLE = "elevated_process_available"
    ELEVATION_FAILED = "elevation_failed"
    UNKNOWN = "unknown"


class AdminIntent(str, Enum):
    INSTALL_SOFTWARE = "install_software"
    MODIFY_SYSTEM_SETTING = "modify_system_setting"
    CREATE_STARTUP_TASK = "create_startup_task"
    EDIT_PROTECTED_FILE = "edit_protected_file"
    RUN_SERVICE_COMMAND = "run_service_command"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AdminCapability:
    state: AdminState
    is_admin_process: bool
    elevated_session_available: bool
    active_sessions: int
    supported_intents: list[str]
    notes: list[str]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data


def classify_admin_intent(command_or_task: str) -> AdminIntent:
    text = command_or_task.lower()
    if re.search(r"\b(choco|winget|msiexec|install-package|pip install --user no)\b", text):
        return AdminIntent.INSTALL_SOFTWARE
    if any(term in text for term in ("set-executionpolicy", "firewall", "registry", "reg add", "netsh", "bcdedit")):
        return AdminIntent.MODIFY_SYSTEM_SETTING
    if any(term in text for term in ("scheduledtask", "startup", "run with highest", "startupeve", "install_startup")):
        return AdminIntent.CREATE_STARTUP_TASK
    if any(term in text for term in ("windows\\system32", "program files", "drivers\\etc", "hosts")):
        return AdminIntent.EDIT_PROTECTED_FILE
    if any(term in text for term in ("service", "start-service", "stop-service", "sc.exe", "restart-service")):
        return AdminIntent.RUN_SERVICE_COMMAND
    return AdminIntent.UNKNOWN


def admin_capability_status() -> dict[str, Any]:
    try:
        admin_now = bool(admin_status().get("is_admin_process"))
    except Exception:
        admin_now = False
    try:
        sessions = list_admin_sessions(include_expired=False)
    except Exception:
        sessions = []
    state = AdminState.ADMIN_AVAILABLE if admin_now else AdminState.NOT_ADMIN
    if sessions and not admin_now:
        state = AdminState.ELEVATED_PROCESS_AVAILABLE
    capability = AdminCapability(
        state=state,
        is_admin_process=admin_now,
        elevated_session_available=bool(sessions),
        active_sessions=len(sessions),
        supported_intents=[item.value for item in AdminIntent if item is not AdminIntent.UNKNOWN],
        notes=[
            "Codex 1 core only classifies/admin state; Codex 2 validates UAC and Windows runtime.",
            "Admin use remains auditable even when unrestricted_mode is the operational default.",
        ],
    )
    return capability.as_dict()

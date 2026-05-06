from __future__ import annotations

from security.admin_gate import admin_allowed, request_admin
from tools.terminal import run_command


def run_admin_command(command: str, reason: str, *, approved: bool = False) -> dict:
    if not approved:
        return request_admin(reason, command)
    if not admin_allowed(True):
        return {"allowed": False, "reason": "admin nao permitido"}
    return run_command(command, approved=True)

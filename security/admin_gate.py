from __future__ import annotations

from security.approval import request_approval
from security.permission_manager import check_action


def request_admin(reason: str, command: str) -> dict:
    decision = check_action("admin", approved=False)
    if decision.allowed:
        return {"allowed": True, "reason": decision.reason, "approval": None, "command": command}
    approval = request_approval("admin", reason, "high", {"command": command})
    return {"allowed": decision.allowed, "reason": decision.reason, "approval": approval}


def admin_allowed(approved: bool) -> bool:
    return check_action("admin", approved=approved).allowed

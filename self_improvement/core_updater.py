from __future__ import annotations

from pathlib import Path

from core.paths import EVE_ROOT
from security.permission_manager import check_action
from self_improvement.rollback_manager import backup_file


def stage_core_file_update(path: str, new_content: str, *, approved: bool = False) -> dict:
    decision = check_action("self_modify_core", approved=approved)
    if not decision.allowed:
        return {"allowed": False, "reason": decision.reason, "requires_approval": decision.requires_approval}
    target = (EVE_ROOT / path).resolve()
    if EVE_ROOT.resolve() not in target.parents:
        raise PermissionError("Core updater so pode alterar ficheiros dentro de D:\\Eve")
    backup = backup_file(target, "core_update")
    target.write_text(new_content, encoding="utf-8")
    return {"allowed": True, "updated": str(target), "backup": str(backup) if backup else None}

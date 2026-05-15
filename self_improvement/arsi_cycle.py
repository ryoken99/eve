from __future__ import annotations

from self_improvement.arsi_policy import arsi_change_allowed
from self_improvement.improvement_cycle import run_improvement_cycle
from self_improvement.verified_self_update import verified_core_update

MAX_ARSI_DEPTH = 3


def run_arsi_cycle(candidate: dict, *, approved: bool = False) -> dict:
    depth = int(candidate.get("depth") or 1)
    if depth > MAX_ARSI_DEPTH:
        return {"applied": False, "framework": "ARSI", "reason": "max recursive depth exceeded", "max_depth": MAX_ARSI_DEPTH}
    policy = arsi_change_allowed(candidate.get("files_changed", []), approved=approved)
    if not policy.get("allowed"):
        return {"applied": False, "framework": "ARSI", "policy": policy, "reason": policy.get("reason")}
    result = run_improvement_cycle(candidate, approved=approved)
    return {"framework": "ARSI", **result}


def arsi_core_update(
    path: str,
    proposed_content: str,
    *,
    tests: list[str] | None = None,
    max_attempts: int = 1,
    approved: bool = False,
) -> dict:
    """Apply an ARSI core change through policy, candidate tests, backup, and rollback evidence.

    Safe files may be improved autonomously. Medium/high-risk files, including core,
    app, security and self_improvement modules, require explicit approval before
    this delegates to the verified self-update writer.
    """
    files_changed = [path]
    policy = arsi_change_allowed(files_changed, approved=approved)
    if not policy.get("allowed"):
        return {
            "framework": "ARSI",
            "status": "blocked",
            "applied": False,
            "policy": policy,
            "reason": policy.get("reason") or "ARSI policy blocked this change",
        }
    risk = policy.get("risk")
    update = verified_core_update(
        path,
        proposed_content,
        tests=tests,
        max_attempts=max_attempts,
        approved=bool(approved or risk == "safe"),
    )
    return {
        "framework": "ARSI",
        "status": update.get("status"),
        "applied": bool(update.get("applied")),
        "policy": policy,
        "update": update,
        "rollback_ready": bool(update.get("backup") or not update.get("applied")),
        "tests_passed": bool((update.get("tests") or {}).get("passed")),
    }

from __future__ import annotations

from self_improvement.arsi_policy import arsi_change_allowed
from self_improvement.improvement_cycle import run_improvement_cycle

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

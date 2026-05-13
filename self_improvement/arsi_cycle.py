from __future__ import annotations

from self_improvement.arsi_policy import arsi_change_allowed
from self_improvement.improvement_cycle import run_improvement_cycle


def run_arsi_cycle(candidate: dict, *, approved: bool = False) -> dict:
    policy = arsi_change_allowed(candidate.get("files_changed", []), approved=approved)
    if not policy.get("allowed"):
        return {"applied": False, "framework": "ARSI", "policy": policy, "reason": policy.get("reason")}
    result = run_improvement_cycle(candidate, approved=approved)
    return {"framework": "ARSI", **result}

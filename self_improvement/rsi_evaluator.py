from __future__ import annotations

from self_improvement.impact_monitor import compare_impact
from self_improvement.rsi_policy import rsi_change_allowed


def evaluate_rsi_candidate(candidate: dict, *, approved: bool = False) -> dict:
    allowed = rsi_change_allowed(candidate.get("files_changed", []), approved=approved)
    impact = compare_impact(float(candidate.get("baseline_metric", 0.0)), float(candidate.get("new_metric", 0.0)), minimum_delta=float(candidate.get("minimum_delta", 0.0)))
    return {"accepted": allowed["allowed"] and impact["improved"], "policy": allowed, "impact": impact}

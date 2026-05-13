from __future__ import annotations

from self_improvement.rsi_policy import classify_change_risk, rsi_change_allowed


def arsi_change_allowed(files_changed: list[str], *, approved: bool = False) -> dict:
    decision = rsi_change_allowed(files_changed, approved=approved)
    decision["framework"] = "ARSI"
    decision["meaning"] = "Autonomous Recursive Self Improvement"
    return decision


def arsi_policy_summary() -> dict:
    return {
        "framework": "ARSI",
        "name": "Autonomous Recursive Self Improvement",
        "safe_autonomy": "safe changes can be proposed, tested, measured, and applied autonomously",
        "medium_high_risk": "approval, tests, backups, and rollback are required",
        "risk_classifier": classify_change_risk(["docs/example.md"]),
    }

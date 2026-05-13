from __future__ import annotations


SAFE_PATHS = ("docs/", "tests/", "lab/candidate_improvements/", "memory/")
HIGH_RISK_PATHS = ("security/", "tools/admin_executor.py", "app/", "core/", "self_improvement/")


def classify_change_risk(files_changed: list[str]) -> str:
    normalized = [path.replace("\\", "/") for path in files_changed]
    if any(path.startswith(HIGH_RISK_PATHS) for path in normalized):
        return "high"
    if all(path.startswith(SAFE_PATHS) for path in normalized):
        return "safe"
    return "medium"


def rsi_change_allowed(files_changed: list[str], *, approved: bool = False) -> dict:
    risk = classify_change_risk(files_changed)
    if risk == "safe":
        return {"allowed": True, "risk": risk}
    if approved:
        return {"allowed": True, "risk": risk, "approval_required": True}
    return {"allowed": False, "risk": risk, "reason": "approval required"}

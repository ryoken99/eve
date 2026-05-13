from __future__ import annotations


def verify_autonomous_action(result: dict, expected: dict | None = None) -> dict:
    if not result.get("ok", result.get("completed", False)):
        return {"verified": False, "reason": "action result was not successful"}
    if not expected:
        return {"verified": True, "reason": "successful result with no extra expectation"}
    missing = [key for key, value in expected.items() if result.get(key) != value]
    return {"verified": not missing, "missing": missing}

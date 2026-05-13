from __future__ import annotations


DEFAULT_BUDGET = {
    "max_actions_per_hour": 5,
    "max_llm_calls_per_day": 20,
    "max_browser_actions_per_day": 10,
    "sensitive_actions": "blocked_without_approval",
}


def budget_allows(kind: str, used: int, *, budget: dict | None = None) -> dict:
    active = budget or DEFAULT_BUDGET
    key = f"max_{kind}"
    limit = active.get(key)
    if limit is None:
        return {"allowed": False, "reason": f"unknown budget kind: {kind}"}
    return {"allowed": used < limit, "used": used, "limit": limit}

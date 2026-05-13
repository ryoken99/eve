from __future__ import annotations


def judge_applicability(item: dict) -> dict:
    relevance = float(item.get("relevance_to_eve", 0.0))
    actionability = float(item.get("actionability", 0.0))
    risk = 0.7 if "admin" in str(item).lower() or "credential" in str(item).lower() else 0.2
    testability = 0.8 if any(word in str(item).lower() for word in ("benchmark", "test", "library", "code")) else 0.4
    expected_gain = round((relevance + actionability + testability - risk) / 3, 3)
    decision = "test_in_lab" if expected_gain >= 0.5 and testability >= 0.6 else "watch" if expected_gain >= 0.3 else "ignore"
    return {"technical_relevance": relevance, "implementation_feasibility": actionability, "risk": risk, "expected_gain": expected_gain, "testability": testability, "decision": decision}

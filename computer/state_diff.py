from __future__ import annotations


def compare_states(before: dict, after: dict) -> dict:
    changed = {}
    keys = set(before) | set(after)
    for key in sorted(keys):
        if before.get(key) != after.get(key):
            changed[key] = {"before": before.get(key), "after": after.get(key)}
    return {"changed": bool(changed), "changes": changed}


def verify_action(before: dict, after: dict, expected_change: dict | None = None) -> dict:
    diff = compare_states(before, after)
    if not expected_change:
        return {"verified": diff["changed"], "diff": diff, "reason": "state changed" if diff["changed"] else "no observable change"}
    missing = []
    for key, value in expected_change.items():
        observed = after.get(key)
        if isinstance(value, str):
            if value.lower() not in str(observed).lower():
                missing.append(key)
        elif observed != value:
            missing.append(key)
    return {"verified": not missing, "diff": diff, "missing": missing, "expected_change": expected_change}

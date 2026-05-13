from __future__ import annotations

from memory.learning_taxonomy import classify_learning_item


def validate_target_folder(text: str, target: str) -> dict:
    expected = classify_learning_item(text)
    return {"valid": expected == target, "expected": expected, "target": target}


def repair_misfiled_learning(items: list[dict]) -> list[dict]:
    repaired = []
    for item in items:
        expected = classify_learning_item(item.get("text", ""))
        repaired.append({**item, "suggested_target": expected, "misfiled": item.get("target") != expected})
    return repaired

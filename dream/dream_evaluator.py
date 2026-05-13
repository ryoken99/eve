from __future__ import annotations


def evaluate_dream(dream: dict) -> dict:
    novelty = min(1.0, len(dream.get("new_connections", [])) / 5)
    usefulness = min(1.0, (len(dream.get("lab_candidates", [])) + len(dream.get("memory_moves", []))) / 5)
    risk = 0.1 if not dream.get("memory_moves") else 0.3
    confidence = round((novelty + usefulness + (1 - risk)) / 3, 3)
    return {"novelty_score": novelty, "usefulness_score": usefulness, "risk_score": risk, "confidence_score": confidence}

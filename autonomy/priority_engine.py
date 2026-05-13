from __future__ import annotations


def score_mission(*, importance: float, urgency: float, risk: float, user_value: float, system_value: float, confidence: float) -> dict:
    score = (importance * 0.25) + (urgency * 0.15) + (user_value * 0.25) + (system_value * 0.2) + (confidence * 0.15) - (risk * 0.3)
    return {"score": round(max(0.0, min(1.0, score)), 3), "inputs": locals()}

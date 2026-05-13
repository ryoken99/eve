from __future__ import annotations


def memory_quality_score(memory: dict) -> dict:
    score = 0.0
    score += 0.25 if memory.get("source") and memory.get("source") != "unknown" else 0
    score += 0.25 if memory.get("confidence", 0) >= 0.7 else 0
    score += 0.2 if memory.get("created_at") else 0
    score += 0.15 if memory.get("layer") in {"medium_term", "long_term"} else 0
    score += 0.15 if not memory.get("contradicts") else -0.15
    return {"score": round(max(0.0, min(1.0, score)), 3), "memory_id": memory.get("id")}

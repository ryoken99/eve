from __future__ import annotations

from memory.semantic_vector.embedding_store import embed_text, load_embedding_index


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def semantic_search(query: str, *, limit: int = 5) -> list[dict]:
    qv = embed_text(query)
    rows = []
    for item in load_embedding_index():
        semantic_score = cosine(qv, item.get("embedding", []))
        metadata = item.get("metadata") or {}
        importance = float(metadata.get("importance", 0.0))
        recency = float(metadata.get("recency", 0.0))
        final = semantic_score + (importance * 0.1) + (recency * 0.05)
        if final > 0:
            rows.append({**item, "semantic_score": round(semantic_score, 4), "final_score": round(final, 4)})
    return sorted(rows, key=lambda row: row["final_score"], reverse=True)[:limit]

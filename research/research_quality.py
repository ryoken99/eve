from __future__ import annotations

from research.source_ranker import source_quality


def score_research_item(item: dict) -> dict:
    title = item.get("title", "")
    summary = item.get("summary", "")
    text = f"{title} {summary}".lower()
    relevance_eve = 0.8 if any(word in text for word in ("agent", "memory", "ui", "browser", "model", "benchmark", "embedding")) else 0.3
    relevance_sandro = 0.8 if any(word in text for word in ("anime", "game", "rpg", "unreal", "training", "martial")) else 0.3
    actionability = 0.8 if any(word in text for word in ("code", "library", "benchmark", "paper", "release")) else 0.4
    quality = source_quality(item.get("url", ""), item.get("source", ""))
    return {**item, "source_quality": quality, "relevance_to_eve": relevance_eve, "relevance_to_sandro": relevance_sandro, "actionability": actionability}

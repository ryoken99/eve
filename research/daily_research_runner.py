from __future__ import annotations

from typing import Any

from core.personality_engine import read_eve_preferences
from research.daily_research_plan import daily_research_tracks
from research.research_inbox import add_research_item


DEFAULT_SANDRO_INTERESTS = [
    "anime game development narrative systems",
    "sports anime training design",
    "RPG Maker Unreal Engine indie games",
    "persistent characters memory NPCs",
]

WORLD_NEWS_QUERIES = [
    "major world technology science culture updates today",
    "latest gaming anime science technology news",
]

TECHNOLOGY_AI_QUERIES = [
    "latest AI agents computer use models",
    "new image video generation AI models",
    "local AI memory retrieval agent tools",
    "OpenAI Anthropic Google DeepMind Meta xAI Mistral Hugging Face latest",
]

PAPER_QUERIES = [
    "arXiv AI agents memory tool use evaluation latest",
    "agentic AI benchmarks memory retrieval papers",
]

OPEN_SOURCE_QUERIES = [
    "GitHub trending AI agents RAG automation",
    "Hugging Face agents open source evaluation memory frameworks",
]


def _stable_preferences() -> list[str]:
    preferences = read_eve_preferences()
    items = []
    for pref in preferences.get("preferences", []):
        if pref.get("status") in {"candidate", "stable"} and float(pref.get("confidence") or 0) >= 0.5:
            items.append(str(pref.get("topic") or "").strip())
    return [item for item in items if item]


def build_daily_research_queries() -> dict[str, list[str]]:
    tracks = daily_research_tracks()
    track_queries = [query for track in tracks for query in track.get("queries", [])]
    eve_interests = _stable_preferences()
    return {
        "sandro_interests": list(dict.fromkeys(DEFAULT_SANDRO_INTERESTS + track_queries[:4])),
        "eve_emerging_interests": eve_interests[:10],
        "world_news": WORLD_NEWS_QUERIES,
        "technology_ai": TECHNOLOGY_AI_QUERIES,
        "papers": PAPER_QUERIES,
        "open_source": OPEN_SOURCE_QUERIES,
    }


def _simulated_items(queries: dict[str, list[str]], max_items: int) -> list[dict[str, Any]]:
    items = []
    for category, category_queries in queries.items():
        for query in category_queries:
            items.append(
                {
                    "source": "daily_research_runner",
                    "title": f"Research plan: {query}",
                    "summary": f"Dry-run query for {category}: {query}",
                    "url": "",
                    "tags": [category, "dry_run"],
                    "raw": {"query": query, "category": category},
                }
            )
            if len(items) >= max_items:
                return items
    return items


def run_daily_research_collection(dry_run: bool = True, max_items: int = 10) -> dict:
    queries = build_daily_research_queries()
    items = _simulated_items(queries, max_items=max_items)
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "queries": queries,
            "items_planned": items,
            "items_added": 0,
        }

    added = []
    for item in items:
        path = add_research_item(
            source=str(item["source"]),
            title=str(item["title"]),
            summary=str(item["summary"]),
            url=str(item.get("url") or ""),
            tags=list(item.get("tags") or []),
            raw=dict(item.get("raw") or {}),
        )
        added.append(str(path))
    return {
        "ok": True,
        "dry_run": False,
        "queries": queries,
        "items_planned": items,
        "items_added": len(added),
        "paths": added,
    }

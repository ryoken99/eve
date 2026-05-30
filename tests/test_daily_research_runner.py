from __future__ import annotations

from research import daily_research_runner


def test_build_daily_research_queries(monkeypatch):
    monkeypatch.setattr(
        daily_research_runner,
        "read_eve_preferences",
        lambda: {"preferences": [{"topic": "memory benchmarks", "status": "stable", "confidence": 0.9}]},
    )

    queries = daily_research_runner.build_daily_research_queries()

    assert "sandro_interests" in queries
    assert "technology_ai" in queries
    assert "memory benchmarks" in queries["eve_emerging_interests"]


def test_run_daily_research_collection_dry_run(monkeypatch):
    monkeypatch.setattr(
        daily_research_runner,
        "build_daily_research_queries",
        lambda: {
            "sandro_interests": ["anime systems"],
            "eve_emerging_interests": [],
            "world_news": [],
            "technology_ai": [],
            "papers": [],
            "open_source": [],
        },
    )

    result = daily_research_runner.run_daily_research_collection(dry_run=True, max_items=1)

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["items_added"] == 0
    assert result["items_planned"][0]["title"].startswith("Research plan")

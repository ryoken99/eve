from __future__ import annotations

import json

from research import research_inbox
from research import research_notes


def test_add_and_list_research_item(tmp_path, monkeypatch):
    monkeypatch.setattr(research_inbox, "RESEARCH_INBOX_DIR", tmp_path / "_inbox" / "research")
    monkeypatch.setattr(research_inbox, "RESEARCH_PROCESSED_DIR", tmp_path / "_processed" / "research")
    monkeypatch.setattr(research_inbox, "RESEARCH_REPORT_PATH", tmp_path / "_processed" / "research" / "report.jsonl")

    path = research_inbox.add_research_item(
        source="unit",
        title="AI memory agents",
        summary="A paper about agent memory and evaluation.",
        tags=["ai"],
    )

    assert path.exists()
    items = research_inbox.list_research_inbox()
    assert len(items) == 1
    assert items[0]["title"] == "AI memory agents"


def test_classify_and_process_research_inbox_dry_run(tmp_path, monkeypatch):
    monkeypatch.setattr(research_inbox, "RESEARCH_INBOX_DIR", tmp_path / "_inbox" / "research")
    monkeypatch.setattr(research_inbox, "RESEARCH_PROCESSED_DIR", tmp_path / "_processed" / "research")
    monkeypatch.setattr(research_inbox, "RESEARCH_REPORT_PATH", tmp_path / "_processed" / "research" / "report.jsonl")
    monkeypatch.setattr(research_notes, "MEMORY_DIR", tmp_path / "memory")

    research_inbox.add_research_item(
        source="unit",
        title="GitHub trending AI agents",
        summary="Open source automation tools for local memory and agents.",
        tags=["technology"],
    )
    result = research_inbox.process_research_inbox(dry_run=True)

    assert result["dry_run"] is True
    assert result["processed_count"] == 1
    categories = result["items"][0]["classification"]["categories"]
    assert "technology_learning" in categories
    assert "lab_candidate" in categories


def test_process_research_inbox_writes_outputs(tmp_path, monkeypatch):
    monkeypatch.setattr(research_inbox, "RESEARCH_INBOX_DIR", tmp_path / "_inbox" / "research")
    monkeypatch.setattr(research_inbox, "RESEARCH_PROCESSED_DIR", tmp_path / "_processed" / "research")
    monkeypatch.setattr(research_inbox, "RESEARCH_REPORT_PATH", tmp_path / "_processed" / "research" / "report.jsonl")
    monkeypatch.setattr(research_notes, "MEMORY_DIR", tmp_path / "memory")
    monkeypatch.setattr(research_inbox, "MEMORY_DIR", tmp_path / "memory")
    monkeypatch.setattr(research_inbox, "LAB_CANDIDATE_DIR", tmp_path / "lab" / "candidate_improvements")

    research_inbox.add_research_item(
        source="unit",
        title="World science news",
        summary="Useful culture and science update for Eve personality learning.",
        tags=["world"],
    )
    result = research_inbox.process_research_inbox(dry_run=False)

    assert result["processed_count"] == 1
    assert research_inbox.RESEARCH_REPORT_PATH.exists()
    report_line = json.loads(research_inbox.RESEARCH_REPORT_PATH.read_text(encoding="utf-8").splitlines()[0])
    assert report_line["title"] == "World science news"

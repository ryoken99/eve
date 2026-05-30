from __future__ import annotations

from pathlib import Path

import autonomy.eve_daily_loop as loop


def test_run_eve_daily_loop_dry_run_returns_dict_and_report(monkeypatch):
    monkeypatch.setattr(loop, "collect_awareness", lambda: {"ok": True, "source": "test"})
    monkeypatch.setattr(loop, "ensure_daily_transcript_files", lambda: {"chat": "chat.jsonl"})
    monkeypatch.setattr(loop, "consolidate", lambda day=None: Path("memory/medium_term/test_summary.md"))
    monkeypatch.setattr(loop, "run_dream_cycle", lambda day=None: {"queue": "lab/queue/test.json"})
    monkeypatch.setattr(loop, "recent_errors", lambda limit=20: [])
    monkeypatch.setattr(loop, "plan_autonomous_system_improvements", lambda max_items=3: {"planned": [], "count": 0})
    monkeypatch.setattr(loop, "capability_audit", lambda: {"summary": {"average_score_10": 9.0}, "points": [], "weakest": []})
    monkeypatch.setattr(loop, "write_capability_audit", lambda: Path("memory/medium_term/eve_capability_roadmap.md"))
    monkeypatch.setattr(loop, "collect_evolution_metrics", lambda: {"capability_average_score": 9.0, "weakest_capability_points": []})
    monkeypatch.setattr(loop, "write_evolution_metrics_report", lambda: Path("memory/medium_term/evolution_metrics/test.md"))

    result = loop.run_eve_daily_loop(cycle_name="unit", dry_run=True)

    assert isinstance(result, dict)
    assert result["cycle_name"] == "unit"
    assert result["dry_run"] is True
    assert "steps" in result
    assert result["reports"]["daily_loop_report"]
    assert Path(result["reports"]["daily_loop_report"]).exists()


def test_each_step_has_required_shape(monkeypatch):
    monkeypatch.setattr(loop, "collect_awareness", lambda: {"ok": True})
    result = loop.run_eve_daily_loop(cycle_name="shape", dry_run=True, max_research_items=1)

    assert result["steps"]
    for step in result["steps"]:
        assert "name" in step
        assert "ok" in step
        assert "result" in step
        assert "error" in step


def test_step_failure_is_recorded_and_loop_continues(monkeypatch):
    def fail_awareness():
        raise RuntimeError("forced awareness failure")

    monkeypatch.setattr(loop, "collect_awareness", fail_awareness)
    monkeypatch.setattr(loop, "ensure_daily_transcript_files", lambda: {"chat": "chat.jsonl"})
    monkeypatch.setattr(loop, "consolidate", lambda day=None: Path("memory/medium_term/test_summary.md"))
    monkeypatch.setattr(loop, "run_dream_cycle", lambda day=None: {"queue": "lab/queue/test.json"})
    monkeypatch.setattr(loop, "recent_errors", lambda limit=20: [])
    monkeypatch.setattr(loop, "plan_autonomous_system_improvements", lambda max_items=3: {"planned": [], "count": 0})
    monkeypatch.setattr(loop, "capability_audit", lambda: {"summary": {"average_score_10": 9.0}, "points": [], "weakest": []})
    monkeypatch.setattr(loop, "write_capability_audit", lambda: Path("memory/medium_term/eve_capability_roadmap.md"))
    monkeypatch.setattr(loop, "collect_evolution_metrics", lambda: {"capability_average_score": 9.0, "weakest_capability_points": []})
    monkeypatch.setattr(loop, "write_evolution_metrics_report", lambda: Path("memory/medium_term/evolution_metrics/test.md"))

    result = loop.run_eve_daily_loop(cycle_name="failure", dry_run=True)

    awareness = result["steps"][0]
    assert result["ok"] is False
    assert awareness["name"] == "awareness"
    assert awareness["ok"] is False
    assert "forced awareness failure" in awareness["error"]
    assert any(step["name"] == "transcripts" and step["ok"] for step in result["steps"])


def test_ensure_eve_daily_loop_schedule_existing(monkeypatch):
    monkeypatch.setattr(loop, "list_cron_jobs", lambda: [{"name": loop.DAILY_LOOP_JOB_NAME, "id": "cron_test"}])

    result = loop.ensure_eve_daily_loop_schedule("6h")

    assert result["ok"] is True
    assert result["status"] == "exists"
    assert result["job"]["id"] == "cron_test"

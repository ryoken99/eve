from __future__ import annotations

from pathlib import Path

from core.evolution_metrics import collect_evolution_metrics, write_evolution_metrics_report


EXPECTED_KEYS = {
    "transcripts_created_today",
    "diary_entries_today",
    "memory_files_changed_today",
    "errors_recorded_today",
    "errors_resolved_today",
    "research_items_today",
    "lab_candidates_today",
    "improvements_proposed_today",
    "improvements_applied_today",
    "autonomy_cycles_today",
    "capability_average_score",
    "weakest_capability_points",
}


def test_collect_evolution_metrics_has_expected_keys():
    metrics = collect_evolution_metrics()

    assert EXPECTED_KEYS.issubset(metrics.keys())
    assert isinstance(metrics["weakest_capability_points"], list)


def test_write_evolution_metrics_report_creates_file():
    path = write_evolution_metrics_report()

    assert isinstance(path, Path)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Evolution Metrics" in text
    assert "capability_average_score" in text

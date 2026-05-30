from __future__ import annotations

from memory.errors import error_review


def test_error_review_dry_run(monkeypatch, tmp_path):
    monkeypatch.setattr(error_review, "ERROR_LESSONS_PATH", tmp_path / "memory" / "errors" / "error_lessons.md")
    monkeypatch.setattr(error_review, "ERROR_CANDIDATES_PATH", tmp_path / "lab" / "candidate_improvements" / "error_candidates.jsonl")
    monkeypatch.setattr(error_review, "ERROR_REVIEW_LOG_DIR", tmp_path / "logs" / "errors")
    monkeypatch.setattr(
        error_review,
        "collect_recent_errors",
        lambda limit=50: [
            {
                "source": "terminal",
                "task": "unit",
                "error_type": "timeout",
                "error_text": "PowerShell timeout while running a tool.",
            }
        ],
    )

    result = error_review.run_error_review(dry_run=True)

    assert result["reviewed_count"] == 1
    assert result["lessons_count"] == 1
    assert result["candidates_count"] == 1
    assert result["reviewed"][0]["classification"]["kind"] == "terminal"


def test_error_review_writes_lessons(monkeypatch, tmp_path):
    monkeypatch.setattr(error_review, "ERROR_LESSONS_PATH", tmp_path / "memory" / "errors" / "error_lessons.md")
    monkeypatch.setattr(error_review, "ERROR_CANDIDATES_PATH", tmp_path / "lab" / "candidate_improvements" / "error_candidates.jsonl")
    monkeypatch.setattr(error_review, "ERROR_REVIEW_LOG_DIR", tmp_path / "logs" / "errors")
    monkeypatch.setattr(
        error_review,
        "collect_recent_errors",
        lambda limit=50: [{"source": "tool", "task": "unit", "error_type": "verification_failed", "error_text": "tool failed"}],
    )

    result = error_review.run_error_review(dry_run=False)

    assert error_review.ERROR_LESSONS_PATH.exists()
    assert error_review.ERROR_CANDIDATES_PATH.exists()
    assert "report_path" in result

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
    assert result["errors_reviewed"] == 1
    assert result["lessons_created"] == 1
    assert result["candidates_created"] == 1
    assert result["duplicates_skipped"] == 0
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


def test_error_review_dry_run_respects_limits_and_writes_no_files(monkeypatch, tmp_path):
    monkeypatch.setattr(error_review, "ERROR_LESSONS_PATH", tmp_path / "memory" / "errors" / "error_lessons.md")
    monkeypatch.setattr(error_review, "ERROR_CANDIDATES_PATH", tmp_path / "lab" / "candidate_improvements" / "error_candidates.jsonl")
    monkeypatch.setattr(error_review, "ERROR_REVIEW_LOG_DIR", tmp_path / "logs" / "errors")
    monkeypatch.setattr(
        error_review,
        "collect_recent_errors",
        lambda limit=50: [
            {"source": "terminal", "task": f"task-{index}", "error_type": "timeout", "error_text": f"timeout {index}"}
            for index in range(5)
        ],
    )

    result = error_review.run_error_review(dry_run=True, max_lessons=2, max_candidates=1)

    assert result["errors_reviewed"] == 5
    assert result["lessons_created"] == 2
    assert result["candidates_created"] == 1
    assert result["limits"]["max_lessons"] == 2
    assert result["limits"]["max_candidates"] == 1
    assert not error_review.ERROR_LESSONS_PATH.exists()
    assert not error_review.ERROR_CANDIDATES_PATH.exists()


def test_error_review_deduplicates_repeated_errors(monkeypatch, tmp_path):
    monkeypatch.setattr(error_review, "ERROR_LESSONS_PATH", tmp_path / "memory" / "errors" / "error_lessons.md")
    monkeypatch.setattr(error_review, "ERROR_CANDIDATES_PATH", tmp_path / "lab" / "candidate_improvements" / "error_candidates.jsonl")
    monkeypatch.setattr(error_review, "ERROR_REVIEW_LOG_DIR", tmp_path / "logs" / "errors")
    repeated = {"source": "tool", "task": "same", "error_type": "verification_failed", "error_text": "same failure"}
    monkeypatch.setattr(error_review, "collect_recent_errors", lambda limit=50: [dict(repeated), dict(repeated), dict(repeated)])

    result = error_review.run_error_review(dry_run=True, max_lessons=10, max_candidates=10)

    assert result["errors_reviewed"] == 3
    assert result["lessons_created"] == 1
    assert result["candidates_created"] == 1
    assert result["duplicates_skipped"] == 2


def test_error_review_real_mode_respects_limits(monkeypatch, tmp_path):
    monkeypatch.setattr(error_review, "ERROR_LESSONS_PATH", tmp_path / "memory" / "errors" / "error_lessons.md")
    monkeypatch.setattr(error_review, "ERROR_CANDIDATES_PATH", tmp_path / "lab" / "candidate_improvements" / "error_candidates.jsonl")
    monkeypatch.setattr(error_review, "ERROR_REVIEW_LOG_DIR", tmp_path / "logs" / "errors")
    monkeypatch.setattr(
        error_review,
        "collect_recent_errors",
        lambda limit=50: [
            {"source": "terminal", "task": f"task-{index}", "error_type": "timeout", "error_text": f"timeout {index}"}
            for index in range(6)
        ],
    )

    result = error_review.run_error_review(dry_run=False, max_lessons=2, max_candidates=1)

    assert result["lessons_created"] == 2
    assert result["candidates_created"] == 1
    assert error_review.ERROR_LESSONS_PATH.read_text(encoding="utf-8").count("## ") == 2
    assert len(error_review.ERROR_CANDIDATES_PATH.read_text(encoding="utf-8").splitlines()) == 1

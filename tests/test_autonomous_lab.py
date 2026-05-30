from __future__ import annotations

from lab import autonomous_lab


def test_create_and_score_lab_candidate(tmp_path, monkeypatch):
    monkeypatch.setattr(autonomous_lab, "LAB_CANDIDATE_DIR", tmp_path / "lab" / "candidate_improvements")
    monkeypatch.setattr(autonomous_lab, "PROMOTED_IMPROVEMENTS_PATH", tmp_path / "lab" / "candidate_improvements" / "promoted.jsonl")

    path = autonomous_lab.create_lab_candidate(
        title="Improve status report",
        origin="research",
        hypothesis="A clearer status report reduces confusion.",
        proposed_change="Add a dry-run report test.",
        expected_benefit="Improve status clarity.",
        risk="low",
        evidence=["Sandro asked for clearer reports."],
    )
    candidates = autonomous_lab.list_lab_candidates()
    scored = autonomous_lab.score_lab_candidate(candidates[0])

    assert path.exists()
    assert len(candidates) == 1
    assert scored["score"] > 0


def test_lab_review_dry_run(tmp_path, monkeypatch):
    monkeypatch.setattr(autonomous_lab, "LAB_CANDIDATE_DIR", tmp_path / "lab" / "candidate_improvements")
    monkeypatch.setattr(autonomous_lab, "PROMOTED_IMPROVEMENTS_PATH", tmp_path / "lab" / "candidate_improvements" / "promoted.jsonl")

    autonomous_lab.create_lab_candidate(
        title="Add report formatter",
        origin="self_reflection",
        hypothesis="Reports become easier to read.",
        proposed_change="Add report formatting test.",
        expected_benefit="Improve report quality.",
        risk="low",
        evidence=["report feedback", "testable change", "low risk"],
    )
    result = autonomous_lab.run_lab_review(dry_run=True)

    assert result["ok"] is True
    assert result["reviewed_count"] == 1

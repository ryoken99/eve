from __future__ import annotations

from core import personality_engine


def test_preference_candidate_and_maturation(tmp_path, monkeypatch):
    monkeypatch.setattr(personality_engine, "EVE_PREFERENCES_PATH", tmp_path / "eve_preferences.json")
    monkeypatch.setattr(personality_engine, "PREFERENCE_CANDIDATES_JSONL", tmp_path / "preference_candidates.jsonl")
    monkeypatch.setattr(personality_engine, "PREFERENCE_EVOLUTION_PATH", tmp_path / "preference_evolution.md")

    candidate = personality_engine.record_preference_candidate(
        topic="agent memory evaluation",
        source="research",
        evidence="Repeated useful papers.",
        confidence=0.8,
        relation_to_sandro="adjacent",
    )
    mature = personality_engine.mature_preference_candidates(min_confidence=0.75)
    preferences = personality_engine.read_eve_preferences()
    report = personality_engine.write_preference_evolution_report()

    assert candidate["status"] == "candidate"
    assert mature["matured_count"] == 1
    assert preferences["preferences"]["agent memory evaluation"]["status"] == "stable"
    assert report.exists()


def test_preference_candidate_accumulates_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(personality_engine, "EVE_PREFERENCES_PATH", tmp_path / "eve_preferences.json")
    monkeypatch.setattr(personality_engine, "PREFERENCE_CANDIDATES_JSONL", tmp_path / "preference_candidates.jsonl")
    monkeypatch.setattr(personality_engine, "PREFERENCE_EVOLUTION_PATH", tmp_path / "preference_evolution.md")

    personality_engine.record_preference_candidate("local autonomy", "research", "First signal", confidence=0.4)
    candidate = personality_engine.record_preference_candidate("local autonomy", "experience", "Second signal", confidence=0.6)

    assert candidate["evidence_count"] == 2
    assert candidate["confidence"] >= 0.6

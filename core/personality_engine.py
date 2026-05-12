from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs


PREF_PATH = MEMORY_DIR / "personality" / "evolving_preferences.md"
PREF_STATE_PATH = MEMORY_DIR / "personality" / "preference_candidates.json"


def _load_preference_state() -> dict:
    ensure_project_dirs()
    if not PREF_STATE_PATH.exists():
        return {"items": {}}
    try:
        return json.loads(PREF_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"items": {}}


def _save_preference_state(state: dict) -> Path:
    PREF_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREF_STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return PREF_STATE_PATH


def update_preference_candidate(topic: str, evidence: str, *, sentiment: str = "positive") -> dict:
    state = _load_preference_state()
    key = topic.strip().lower()
    item = state.setdefault("items", {}).setdefault(
        key,
        {"topic": topic.strip(), "status": "candidate", "evidence": [], "score": 0, "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")},
    )
    delta = 1 if sentiment != "negative" else -1
    item["score"] = int(item.get("score") or 0) + delta
    item.setdefault("evidence", []).append(
        {"timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "text": evidence.strip(), "sentiment": sentiment}
    )
    if item["score"] >= 3:
        item["status"] = "stable"
    elif item["score"] >= 2:
        item["status"] = "reinforced"
    elif item["score"] < 0:
        item["status"] = "rejected"
    else:
        item["status"] = "candidate"
    _save_preference_state(state)
    return item


def add_preference(preference: str, reason: str = "") -> Path:
    ensure_project_dirs()
    candidate = update_preference_candidate(preference, reason or "manual preference note")
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with PREF_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"\n- {timestamp}: {preference.strip()} | estado: {candidate['status']} | score: {candidate['score']}")
        if reason.strip():
            handle.write(f" | razao: {reason.strip()}")
        handle.write("\n")
    return PREF_PATH


def read_preferences() -> str:
    if not PREF_PATH.exists():
        return ""
    return PREF_PATH.read_text(encoding="utf-8")


def score_options(options: list[str]) -> list[dict]:
    preferences = read_preferences().lower()
    weighted_terms = ["memoria", "vision", "ocr", "agente", "autonomia", "seguranca", "lab", "self", "browser"]
    scored = []
    for option in options:
        text = option.lower()
        score = 0
        for term in weighted_terms:
            if term in text:
                score += 2
            if term in preferences:
                score += 1
        scored.append({"option": option, "score": score})
    return sorted(scored, key=lambda item: item["score"], reverse=True)

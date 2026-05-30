from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs


PREF_PATH = MEMORY_DIR / "personality" / "evolving_preferences.md"
PREF_STATE_PATH = MEMORY_DIR / "personality" / "preference_candidates.json"
EVE_PREFERENCES_PATH = MEMORY_DIR / "personality" / "eve_preferences.json"
PREFERENCE_CANDIDATES_JSONL = MEMORY_DIR / "personality" / "preference_candidates.jsonl"
PREFERENCE_EVOLUTION_PATH = MEMORY_DIR / "personality" / "preference_evolution.md"


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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_eve_preferences() -> dict:
    ensure_project_dirs()
    if not EVE_PREFERENCES_PATH.exists():
        return {"preferences": {}}
    try:
        data = json.loads(EVE_PREFERENCES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"preferences": {}}
    return data if isinstance(data, dict) else {"preferences": {}}


def _save_eve_preferences(data: dict) -> Path:
    EVE_PREFERENCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVE_PREFERENCES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return EVE_PREFERENCES_PATH


def record_preference_candidate(
    topic: str,
    source: str,
    evidence: str,
    sentiment: str = "positive",
    confidence: float = 0.5,
    relation_to_sandro: str = "inherited",
) -> dict:
    ensure_project_dirs()
    confidence = max(0.0, min(1.0, float(confidence)))
    topic_clean = topic.strip()
    key = topic_clean.lower()
    data = _load_eve_preferences()
    prefs = data.setdefault("preferences", {})
    item = prefs.setdefault(
        key,
        {
            "topic": topic_clean,
            "status": "candidate",
            "origin": source if source in {"sandro", "research", "experience", "self_reflection"} else "research",
            "relation_to_sandro": relation_to_sandro,
            "confidence": 0.0,
            "evidence_count": 0,
            "last_seen": "",
        },
    )
    item["topic"] = item.get("topic") or topic_clean
    item["relation_to_sandro"] = relation_to_sandro
    item["last_seen"] = _now()
    item["evidence_count"] = int(item.get("evidence_count") or 0) + 1
    old_confidence = float(item.get("confidence") or 0.0)
    delta = confidence if sentiment != "negative" else -confidence
    item["confidence"] = round(max(0.0, min(1.0, max(old_confidence, max(0.0, delta)))), 3)
    if sentiment == "negative" and item["confidence"] < 0.25:
        item["status"] = "rejected"
    elif item.get("status") != "stable":
        item["status"] = "candidate"
    else:
        item["status"] = "stable"
    _save_eve_preferences(data)
    row = {
        "timestamp": _now(),
        "topic": topic_clean,
        "source": source,
        "evidence": evidence,
        "sentiment": sentiment,
        "confidence": confidence,
        "relation_to_sandro": relation_to_sandro,
        "preference": item,
    }
    PREFERENCE_CANDIDATES_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with PREFERENCE_CANDIDATES_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return item


def mature_preference_candidates(min_confidence: float = 0.75) -> dict:
    data = _load_eve_preferences()
    matured: list[dict] = []
    for item in data.setdefault("preferences", {}).values():
        if item.get("status") == "candidate" and float(item.get("confidence") or 0.0) >= min_confidence:
            item["status"] = "stable"
            item["last_seen"] = _now()
            matured.append(dict(item))
    _save_eve_preferences(data)
    return {"ok": True, "matured_count": len(matured), "matured": matured, "path": str(EVE_PREFERENCES_PATH)}


def read_eve_preferences() -> dict:
    return _load_eve_preferences()


def write_preference_evolution_report() -> Path:
    data = _load_eve_preferences()
    lines = ["# Eve Preference Evolution", ""]
    for item in sorted(data.get("preferences", {}).values(), key=lambda row: (row.get("status", ""), row.get("topic", ""))):
        lines.extend(
            [
                f"## {item.get('topic')}",
                f"- Status: {item.get('status')}",
                f"- Origin: {item.get('origin')}",
                f"- Relation to Sandro: {item.get('relation_to_sandro')}",
                f"- Confidence: {item.get('confidence')}",
                f"- Evidence count: {item.get('evidence_count')}",
                f"- Last seen: {item.get('last_seen')}",
                "",
            ]
        )
    PREFERENCE_EVOLUTION_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFERENCE_EVOLUTION_PATH.write_text("\n".join(lines), encoding="utf-8")
    return PREFERENCE_EVOLUTION_PATH

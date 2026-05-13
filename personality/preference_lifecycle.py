from __future__ import annotations

import json
from datetime import datetime, timezone

from core.paths import MEMORY_DIR, ensure_project_dirs


PREFERENCES_PATH = MEMORY_DIR / "personality" / "preference_lifecycle.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load() -> dict[str, dict]:
    ensure_project_dirs()
    if not PREFERENCES_PATH.exists():
        return {}
    try:
        return json.loads(PREFERENCES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(rows: dict[str, dict]):
    PREFERENCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFERENCES_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def update_preference(topic: str, evidence: str, *, source: str = "experience", sentiment: str = "positive") -> dict:
    rows = _load()
    row = rows.get(topic) or {
        "topic": topic,
        "status": "candidate",
        "evidence": [],
        "counter_evidence": [],
        "reason": "",
        "first_seen": _now(),
        "last_seen": _now(),
        "stability_score": 0.0,
        "source": source,
    }
    target = "counter_evidence" if sentiment == "negative" else "evidence"
    row[target].append({"text": evidence, "source": source, "timestamp": _now()})
    row["last_seen"] = _now()
    positive = len(row["evidence"])
    negative = len(row["counter_evidence"])
    row["stability_score"] = max(0.0, round((positive - negative) / 3, 3))
    if negative:
        row["status"] = "conflicted" if positive else "rejected"
    elif positive >= 3:
        row["status"] = "stable"
    elif positive >= 2:
        row["status"] = "reinforced"
    else:
        row["status"] = "candidate"
    row["reason"] = f"{positive} positive evidence items, {negative} counter-evidence items"
    rows[topic] = row
    _save(rows)
    return row

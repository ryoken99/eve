from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from core.paths import LAB_DIR, ensure_project_dirs


def create_candidate(title: str, hypothesis: str, metric: str = "manual_review") -> Path:
    ensure_project_dirs()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in title.lower()).strip("_")
    path = LAB_DIR / "candidate_improvements" / f"{safe}.json"
    payload = {
        "title": title,
        "hypothesis": hypothesis,
        "metric": metric,
        "status": "candidate",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "decision": None,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def list_candidates() -> list[str]:
    ensure_project_dirs()
    return sorted(p.stem for p in (LAB_DIR / "candidate_improvements").glob("*.json"))


def record_candidate_result(title: str, *, metric_value: float, threshold: float, notes: str = "") -> dict:
    ensure_project_dirs()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in title.lower()).strip("_")
    path = LAB_DIR / "candidate_improvements" / f"{safe}.json"
    if not path.exists():
        raise FileNotFoundError(f"candidate not found: {title}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    decision = "accept" if float(metric_value) >= float(threshold) else "observe"
    if float(metric_value) < 0:
        decision = "reject"
    result = {
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
        "metric_value": metric_value,
        "threshold": threshold,
        "decision": decision,
        "notes": notes,
    }
    payload.setdefault("results", []).append(result)
    payload["decision"] = decision
    payload["status"] = "decided" if decision in {"accept", "reject"} else "observing"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report = LAB_DIR / "reports" / "candidate_decisions.jsonl"
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"title": title, "path": str(path), "result": result}, ensure_ascii=False) + "\n")
    return {"candidate": str(path), "report": str(report), "result": result}

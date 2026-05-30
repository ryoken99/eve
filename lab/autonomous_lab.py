from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import LAB_DIR, ensure_project_dirs


LAB_CANDIDATE_DIR = LAB_DIR / "candidate_improvements"
PROMOTED_IMPROVEMENTS_PATH = LAB_CANDIDATE_DIR / "promoted_improvements.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(title: str) -> str:
    stem = "".join(ch.lower() if ch.isalnum() else "_" for ch in title).strip("_")
    return f"lab_{datetime.now().strftime('%Y%m%d%H%M%S')}_{stem[:48] or 'candidate'}"


def _ensure_dirs() -> None:
    ensure_project_dirs()
    LAB_CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)


def _candidate_path(candidate_id: str) -> Path:
    return LAB_CANDIDATE_DIR / f"{candidate_id}.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def create_lab_candidate(
    title: str,
    origin: str,
    hypothesis: str,
    proposed_change: str,
    expected_benefit: str,
    risk: str = "low",
    evidence: list[str] | None = None,
) -> Path:
    _ensure_dirs()
    candidate_id = _safe_id(title)
    now = _now()
    payload = {
        "id": candidate_id,
        "title": title,
        "origin": origin,
        "hypothesis": hypothesis,
        "proposed_change": proposed_change,
        "expected_benefit": expected_benefit,
        "risk": risk,
        "evidence": evidence or [],
        "score": 0.0,
        "status": "open",
        "created_at": now,
        "updated_at": now,
    }
    path = _candidate_path(candidate_id)
    _write_json(path, payload)
    return path


def list_lab_candidates(status: str = "open") -> list[dict]:
    _ensure_dirs()
    candidates: list[dict[str, Any]] = []
    for path in sorted(LAB_CANDIDATE_DIR.glob("lab_*.json")):
        try:
            candidate = _read_json(path)
        except Exception:
            continue
        if status == "all" or candidate.get("status") == status:
            candidate["_path"] = str(path)
            candidates.append(candidate)
    return candidates


def score_lab_candidate(candidate: dict) -> dict:
    risk = str(candidate.get("risk") or "low").lower()
    evidence_count = len(candidate.get("evidence") or [])
    benefit_text = str(candidate.get("expected_benefit") or "").lower()
    change_text = str(candidate.get("proposed_change") or "").lower()
    score = 0.35
    score += min(evidence_count, 5) * 0.08
    if any(word in benefit_text for word in ("reduce", "melhor", "improve", "corrigir", "fix", "faster")):
        score += 0.18
    if any(word in change_text for word in ("test", "dry-run", "relatorio", "report", "status")):
        score += 0.1
    score -= {"low": 0.0, "medium": 0.15, "high": 0.3, "critical": 0.6}.get(risk, 0.2)
    score = max(0.0, min(1.0, round(score, 3)))
    result = dict(candidate)
    result["score"] = score
    result["score_reason"] = "Heuristic score from evidence, expected benefit, proposed safety, and risk."
    return result


def promote_candidate_to_improvement(candidate_id: str, dry_run: bool = True) -> dict:
    _ensure_dirs()
    path = _candidate_path(candidate_id)
    if not path.exists():
        raise FileNotFoundError(candidate_id)
    candidate = _read_json(path)
    scored = score_lab_candidate(candidate)
    result = {
        "candidate_id": candidate_id,
        "dry_run": dry_run,
        "score": scored["score"],
        "status": "would_promote" if dry_run else "promoted",
        "target": str(PROMOTED_IMPROVEMENTS_PATH),
    }
    if dry_run:
        return result

    now = _now()
    candidate["status"] = "promoted"
    candidate["score"] = scored["score"]
    candidate["updated_at"] = now
    _write_json(path, candidate)
    with PROMOTED_IMPROVEMENTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"promoted_at": now, "candidate": candidate}, ensure_ascii=False) + "\n")
    return result


def run_lab_review(max_candidates: int = 5, dry_run: bool = True) -> dict:
    candidates = list_lab_candidates(status="open")[:max_candidates]
    scored = [score_lab_candidate(candidate) for candidate in candidates]
    scored.sort(key=lambda item: item.get("score", 0), reverse=True)
    promotions = []
    for candidate in scored:
        if float(candidate.get("score") or 0) >= 0.65:
            promotions.append(promote_candidate_to_improvement(str(candidate["id"]), dry_run=dry_run))
    return {
        "ok": True,
        "dry_run": dry_run,
        "reviewed_count": len(scored),
        "promotion_candidates_count": len(promotions),
        "candidates": scored,
        "promotions": promotions,
    }

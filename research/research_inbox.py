from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import EVE_ROOT, LAB_DIR, MEMORY_DIR, ensure_project_dirs
from research.research_notes import (
    append_personality_learning,
    append_research_candidate,
    append_technology_learning,
    append_world_learning,
)


RESEARCH_INBOX_DIR = MEMORY_DIR / "_inbox" / "research"
RESEARCH_PROCESSED_DIR = MEMORY_DIR / "_processed" / "research"
RESEARCH_REPORT_PATH = RESEARCH_PROCESSED_DIR / "research_inbox_report.jsonl"
LAB_CANDIDATE_DIR = LAB_DIR / "candidate_improvements"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _ensure_dirs() -> None:
    ensure_project_dirs()
    for path in (
        RESEARCH_INBOX_DIR,
        RESEARCH_PROCESSED_DIR,
        MEMORY_DIR / "world",
        MEMORY_DIR / "technology",
        MEMORY_DIR / "personality",
        LAB_CANDIDATE_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _safe_name(text: str) -> str:
    clean = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in text.lower()).strip("_")
    return clean[:80] or "research_item"


def _read_item(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(data, dict):
        data.setdefault("_path", str(path))
        return data
    return None


def add_research_item(
    source: str,
    title: str,
    summary: str,
    url: str = "",
    tags: list[str] | None = None,
    raw: dict | None = None,
) -> Path:
    _ensure_dirs()
    item_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    payload = {
        "id": item_id,
        "source": source,
        "title": title,
        "summary": summary,
        "url": url,
        "tags": tags or [],
        "raw": raw or {},
        "status": "inbox",
        "created_at": _now(),
        "updated_at": _now(),
    }
    path = RESEARCH_INBOX_DIR / f"{item_id}_{_safe_name(title)}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def list_research_inbox(limit: int = 20) -> list[dict]:
    _ensure_dirs()
    items: list[dict[str, Any]] = []
    for path in sorted(RESEARCH_INBOX_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        item = _read_item(path)
        if item:
            items.append(item)
        if len(items) >= limit:
            break
    return items


def classify_research_item(item: dict) -> dict:
    title = str(item.get("title") or "")
    summary = str(item.get("summary") or "")
    tags = [str(tag).lower() for tag in (item.get("tags") or [])]
    text = f"{title} {summary} {' '.join(tags)}".lower()
    categories: list[str] = []
    reasons: list[str] = []
    if any(term in text for term in ("ai", "agent", "model", "openai", "anthropic", "deepmind", "hugging face", "github", "paper", "arxiv", "memory", "retrieval", "automation")):
        categories.append("technology_learning")
        reasons.append("technology/AI/open-source signal")
    if any(term in text for term in ("world", "news", "science", "culture", "game", "anime", "market", "society")):
        categories.append("world_learning")
        reasons.append("world/culture/news signal")
    if any(term in text for term in ("taste", "preference", "interest", "style", "aesthetic", "story", "narrative", "curiosity")):
        categories.append("personality_interest")
        reasons.append("preference or interest signal")
    if any(term in text for term in ("experiment", "benchmark", "evaluation", "prototype", "tool", "improve", "failure", "bug", "workflow")):
        categories.append("lab_candidate")
        reasons.append("testable improvement signal")
    if not categories:
        categories.append("needs_review")
        reasons.append("no strong deterministic category")
    if "spam" in text or len(text.strip()) < 20:
        categories = ["ignore"]
        reasons = ["too little signal or spam-like"]
    return {
        "item_id": item.get("id"),
        "categories": sorted(set(categories)),
        "confidence": 0.75 if categories != ["needs_review"] else 0.4,
        "reasons": reasons,
    }


def _append_report(row: dict[str, Any]) -> None:
    RESEARCH_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with RESEARCH_REPORT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _lab_candidate_path(item: dict, classification: dict) -> Path:
    path = LAB_CANDIDATE_DIR / f"research_{item.get('id')}.json"
    payload = {
        "id": f"research_{item.get('id')}",
        "title": item.get("title"),
        "origin": "research",
        "hypothesis": item.get("summary"),
        "proposed_change": "Review this research item as a possible Eve improvement.",
        "expected_benefit": "Potential improvement to Eve capability, workflow, or knowledge.",
        "risk": "low",
        "evidence": [item.get("url") or item.get("source") or ""],
        "score": classification.get("confidence", 0.5),
        "status": "open",
        "created_at": _now(),
        "updated_at": _now(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def process_research_inbox(limit: int = 10, dry_run: bool = False) -> dict:
    _ensure_dirs()
    processed: list[dict[str, Any]] = []
    for item in list_research_inbox(limit=limit):
        path = Path(str(item.get("_path")))
        classification = classify_research_item(item)
        categories = classification["categories"]
        destinations: list[str] = []
        text = f"{item.get('title')}: {item.get('summary')} {item.get('url')}".strip()
        if not dry_run:
            if "world_learning" in categories:
                destinations.append(str(append_world_learning(text)))
            if "technology_learning" in categories:
                destinations.append(str(append_technology_learning(text)))
            if "personality_interest" in categories:
                destinations.append(str(append_personality_learning(text)))
            if "lab_candidate" in categories:
                destinations.append(str(_lab_candidate_path(item, classification)))
            if "needs_review" in categories:
                destinations.append(str(append_research_candidate(f"Needs review: {text}")))
            if "ignore" not in categories:
                processed_path = RESEARCH_PROCESSED_DIR / path.name
                shutil.copy2(path, processed_path)
                path.unlink(missing_ok=True)
                destinations.append(str(processed_path))
        row = {
            "timestamp": _now(),
            "item_id": item.get("id"),
            "title": item.get("title"),
            "dry_run": dry_run,
            "classification": classification,
            "destinations": destinations,
        }
        if not dry_run:
            _append_report(row)
        processed.append(row)
    return {"ok": True, "dry_run": dry_run, "processed_count": len(processed), "items": processed}

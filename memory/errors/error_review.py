from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import LAB_DIR, LOGS_DIR, MEMORY_DIR, ensure_project_dirs
from memory.errors.error_memory import error_to_lesson, recent_errors


ERROR_LESSONS_PATH = MEMORY_DIR / "errors" / "error_lessons.md"
ERROR_CANDIDATES_PATH = LAB_DIR / "candidate_improvements" / "error_candidates.jsonl"
ERROR_REVIEW_LOG_DIR = LOGS_DIR / "errors"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _ensure_dirs() -> None:
    ensure_project_dirs()
    ERROR_LESSONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ERROR_CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    ERROR_REVIEW_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _text(error: dict[str, Any]) -> str:
    return " ".join(
        str(error.get(key) or "")
        for key in ("source", "task", "error_type", "error_text", "message", "lesson")
    ).lower()


def collect_recent_errors(limit: int = 50) -> list[dict]:
    return recent_errors(limit=limit)


def classify_error(error: dict) -> dict:
    text = _text(error)
    source = str(error.get("source") or "").lower()
    error_type = str(error.get("error_type") or "").lower()
    kind = "unknown"
    if "terminal" in source or "powershell" in text or "exit_" in error_type:
        kind = "terminal"
    elif "browser" in source or "ui" in source or "ocr" in text:
        kind = "browser_ui"
    elif "memory" in source or "chroma" in text or "vector" in text:
        kind = "memory"
    elif "tool" in source or "verification_failed" in error_type:
        kind = "tool"
    elif "sandro" in text or "corrig" in text or "errado" in text:
        kind = "sandro_correction"
    elif "config" in text or "missing" in error_type or "dependency" in text:
        kind = "configuration"

    severity = "low"
    if any(marker in text for marker in ("critical", "crash", "traceback", "permission", "secret", "token")):
        severity = "high"
    elif any(marker in text for marker in ("timeout", "failed", "erro", "error", "exception")):
        severity = "medium"

    return {
        "kind": kind,
        "severity": severity,
        "source": error.get("source") or "unknown",
        "error_type": error.get("error_type") or "unknown",
        "reason": f"Classified as {kind} from source/text markers.",
    }


def create_lesson_from_error(error: dict) -> dict:
    classification = classify_error(error)
    lesson = error_to_lesson(error)
    return {
        "created_at": _now(),
        "source": error.get("source") or "unknown",
        "task": error.get("task") or "",
        "error_type": error.get("error_type") or "unknown",
        "error_kind": classification["kind"],
        "severity": classification["severity"],
        "lesson": lesson,
        "status": "active",
    }


def create_improvement_candidate_from_error(error: dict) -> dict:
    classification = classify_error(error)
    candidate_id = (
        f"err_{datetime.now().strftime('%Y%m%d%H%M%S')}_"
        f"{classification['kind']}_{str(error.get('error_type') or 'unknown')}"
    )
    return {
        "candidate_id": candidate_id,
        "created_at": _now(),
        "origin": "error",
        "problem": str(error.get("error_text") or error.get("message") or error.get("error_type") or "")[:1000],
        "evidence": {
            "source": error.get("source") or "unknown",
            "task": error.get("task") or "",
            "error_type": error.get("error_type") or "unknown",
        },
        "proposed_fix": create_lesson_from_error(error)["lesson"],
        "target_files": [],
        "risk_level": "medium" if classification["severity"] == "high" else "low",
        "requires_approval": classification["severity"] in {"medium", "high"},
        "test_plan": "Reproduce the failure, add or run the smallest related check, then verify the same action succeeds.",
        "rollback_plan": "Revert only the candidate patch or disable the new behavior; never delete transcripts or memory.",
        "status": "proposed",
    }


def _append_lesson_markdown(lessons: list[dict]) -> None:
    if not lessons:
        return
    with ERROR_LESSONS_PATH.open("a", encoding="utf-8") as handle:
        for lesson in lessons:
            handle.write(
                "\n".join(
                    [
                        "",
                        f"## {lesson['created_at']} - {lesson['error_kind']}",
                        f"- Source: {lesson['source']}",
                        f"- Error type: {lesson['error_type']}",
                        f"- Severity: {lesson['severity']}",
                        f"- Lesson: {lesson['lesson']}",
                        f"- Status: {lesson['status']}",
                        "",
                    ]
                )
            )


def _append_candidates(candidates: list[dict]) -> None:
    if not candidates:
        return
    with ERROR_CANDIDATES_PATH.open("a", encoding="utf-8") as handle:
        for candidate in candidates:
            handle.write(json.dumps(candidate, ensure_ascii=False) + "\n")


def run_error_review(limit: int = 50, dry_run: bool = False) -> dict:
    _ensure_dirs()
    errors = collect_recent_errors(limit=limit)
    reviewed = []
    lessons = []
    candidates = []
    for error in errors:
        classification = classify_error(error)
        lesson = create_lesson_from_error(error)
        candidate = create_improvement_candidate_from_error(error)
        reviewed.append({"error": error, "classification": classification})
        lessons.append(lesson)
        candidates.append(candidate)

    report = {
        "ok": True,
        "dry_run": dry_run,
        "reviewed_count": len(reviewed),
        "lessons_count": len(lessons),
        "candidates_count": len(candidates),
        "lessons_path": str(ERROR_LESSONS_PATH),
        "candidates_path": str(ERROR_CANDIDATES_PATH),
        "reviewed": reviewed,
    }
    if dry_run:
        return report

    _append_lesson_markdown(lessons)
    _append_candidates(candidates)
    log_path = ERROR_REVIEW_LOG_DIR / f"error_review_{_today()}.md"
    lines = ["# Error Review", "", f"- Created: {_now()}", f"- Errors reviewed: {len(reviewed)}", ""]
    for item in reviewed:
        classification = item["classification"]
        error = item["error"]
        lines.extend(
            [
                f"## {classification['kind']} / {classification['severity']}",
                f"- Source: {error.get('source') or 'unknown'}",
                f"- Error type: {error.get('error_type') or 'unknown'}",
                f"- Summary: {str(error.get('error_text') or error.get('message') or '')[:500]}",
                "",
            ]
        )
    log_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    report["report_path"] = str(log_path)
    return report

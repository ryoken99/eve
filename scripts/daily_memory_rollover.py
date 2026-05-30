from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


EVE_ROOT = Path(__file__).resolve().parents[1]
MEMORY_ROOT = EVE_ROOT / "memory"

ROLLUP_DIR = MEMORY_ROOT / "transcripts" / "daily_rollups"
CLASSIFICATIONS_DIR = MEMORY_ROOT / "_processed" / "classifications"
CHUNKS_DIR = MEMORY_ROOT / "_processed" / "chunks"
DREAM_DIR = MEMORY_ROOT / "dreams" / "daily"
ERROR_REVIEW_DIR = MEMORY_ROOT / "_processed" / "errors"
TOOL_REVIEW_DIR = MEMORY_ROOT / "_processed" / "tools"
AUTONOMY_DIR = MEMORY_ROOT / "_processed" / "autonomy"
PROMOTION_DIR = MEMORY_ROOT / "_processed" / "promotions"
SYSTEM_DIR = MEMORY_ROOT / "_system"
SESSION_STATE_DIR = MEMORY_ROOT / "runtime" / "session_state"
MEMORY_DAY_OVERRIDE_PATH = SESSION_STATE_DIR / "memory_day_override.json"
SESSION_ROOT = MEMORY_ROOT / "runtime" / "sessions"
SESSION_ACTIVE_DIR = SESSION_ROOT / "active"
SESSION_ARCHIVE_DIR = SESSION_ROOT / "archive"
SESSION_HANDOFF_DIR = SESSION_ROOT / "handoffs"
SESSION_STATE_DIR_NEW = SESSION_ROOT / "state"
CURRENT_SESSION_PATH = SESSION_STATE_DIR_NEW / "current_session.json"
LATEST_HANDOFF_PATH = SESSION_HANDOFF_DIR / "latest_handoff.md"
ERROR_BACKLOG_PATH = MEMORY_ROOT / "medium_term" / "error_backlog" / "error_backlog.jsonl"
TOOL_LESSONS_PATH = MEMORY_ROOT / "medium_term" / "tool_lessons" / "tool_lessons.jsonl"
AUTONOMY_CANDIDATES_PATH = MEMORY_ROOT / "medium_term" / "autonomy_candidates" / "arsi_candidates.jsonl"
SHORT_TERM_PENDING_DIR = MEMORY_ROOT / "short_term" / "pending"
MEDIUM_TERM_CANDIDATES_DIR = MEMORY_ROOT / "medium_term"

CHANNELS = ("terminal", "telegram", "webui", "tools", "errors", "system")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def default_rollover_date() -> datetime:
    now = datetime.now()
    return now - timedelta(days=1) if now.hour < 3 else now


def parse_date(date_text: str) -> datetime:
    return datetime.strptime(date_text, "%Y-%m-%d")


def content_hash(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8", errors="replace")).hexdigest()


def stable_id(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8", errors="replace")).hexdigest()[:24]


def sanitize_excerpt(text: str, max_chars: int = 800) -> str:
    flat = re.sub(r"\s+", " ", str(text or "")).strip()
    return flat[:max_chars].rstrip()


def transcript_path(channel: str, date_key: str) -> Path:
    if channel in {"tools", "errors"}:
        return MEMORY_ROOT / "transcripts" / channel / f"{date_key}.jsonl"
    return MEMORY_ROOT / "transcripts" / "raw" / channel / f"{date_key}.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append(
                {
                    "timestamp": "",
                    "channel": path.parent.name,
                    "speaker": "system",
                    "message": line,
                    "metadata": {"parse_error": True, "line_number": line_number},
                }
            )
    return rows


def load_transcripts(date_key: str) -> dict[str, list[dict[str, Any]]]:
    return {channel: read_jsonl(transcript_path(channel, date_key)) for channel in CHANNELS}


def ensure_dirs() -> None:
    for path in (
        ROLLUP_DIR,
        CLASSIFICATIONS_DIR,
        CHUNKS_DIR,
        DREAM_DIR,
        ERROR_REVIEW_DIR,
        TOOL_REVIEW_DIR,
        AUTONOMY_DIR,
        PROMOTION_DIR,
        SHORT_TERM_PENDING_DIR,
        ERROR_BACKLOG_PATH.parent,
        TOOL_LESSONS_PATH.parent,
        AUTONOMY_CANDIDATES_PATH.parent,
        MEMORY_ROOT / "long_term" / "confirmed",
        SESSION_ACTIVE_DIR,
        SESSION_ARCHIVE_DIR,
        SESSION_HANDOFF_DIR,
        SESSION_STATE_DIR_NEW,
    ):
        path.mkdir(parents=True, exist_ok=True)


def message_from_entry(entry: dict[str, Any]) -> str:
    value = entry.get("message")
    if value is None:
        value = (entry.get("payload") or {}).get("content")
    return str(value or "").strip()


def metadata_from_entry(entry: dict[str, Any]) -> dict[str, Any]:
    metadata = entry.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def infer_category(text: str, channel: str, metadata: dict[str, Any]) -> tuple[str, str | None]:
    lowered = text.lower()
    if channel == "errors":
        return "error", None
    if channel == "tools":
        tool_name = str(metadata.get("tool_name") or "").lower()
        if "error" in lowered or metadata.get("ok") is False:
            return "error", "tool_failure"
        if any(term in tool_name for term in ("telegram", "browser", "web", "memory", "vector", "rollover")):
            return "tooling", None
        return "tooling", None
    if channel == "system":
        if any(term in lowered for term in ("autonomy", "arsi", "self improvement", "melhoria", "daemon")):
            return "autonomy", None
        return "technical", None
    if any(term in lowered for term in ("erro", "error", "exception", "traceback", "failed", "falha", "crash")):
        return "error", None
    if any(term in lowered for term in ("bubu", "marta", "saude", "saúde", "dor", "medicação", "medicacao", "peso")):
        return "bubu_private", None
    if any(term in lowered for term in ("sandro", "tu és", "tu es", "meu utilizador", "criador da eve")):
        return "sandro_core", None
    if any(term in lowered for term in ("eve", "minha casa", "pc2", "pc 2", "pc1", "pc 1", "e:\\eve", "d:\\eve")):
        return "pc_runtime", None
    if any(term in lowered for term in ("lifepath", "helix", "echoes of eternity", "kaelen", "lore", "simulação", "simulacao")):
        return "lore_simulation", None
    if any(term in lowered for term in ("mia kinsky", "entity", "entities", "entidade")):
        return "entities", None
    if any(term in lowered for term in ("master coder", "mastercoder", "mastermind", "agent", "agente")):
        return "agents", None
    if any(term in lowered for term in ("linguagem criada", "conlang", "tradutor", "idioma")):
        return "language", None
    if any(term in lowered for term in ("projecto", "projeto", "rpg", "unreal", "rpg maker", "web ui", "telegram bridge")):
        return "projects", None
    if any(term in lowered for term in ("melhorar", "corrigir", "autonomia", "arsi", "self improvement", "rollback")):
        return "autonomy", None
    return "unknown", None


def infer_sensitivity(text: str, category: str) -> str:
    lowered = text.lower()
    if category == "bubu_private" or any(term in lowered for term in ("bubu", "marta", "saude", "saúde", "dor", "medicação", "medicacao")):
        return "health_private|relationship_private"
    if category in {"pc_runtime", "technical", "tooling", "error", "autonomy"}:
        return "technical_private"
    if category == "lore_simulation":
        return "lore"
    if category in {"sandro_core", "projects", "agents", "language", "entities"}:
        return "sensitive_private" if "sandro" in lowered else "private"
    if category == "unknown":
        return "unknown"
    return "private"


def infer_importance(text: str, channel: str, category: str, metadata: dict[str, Any]) -> tuple[int, float, str]:
    lowered = text.lower()
    if metadata.get("parse_error"):
        return 3, 0.70, "transcript_parse_error_needs_review"
    if category == "error":
        return 4, 0.82, "technical_error_requires_backlog_review"
    if category == "bubu_private":
        return 4, 0.80, "private_health_or_relationship_context_requires_care"
    if category in {"pc_runtime", "sandro_core"} and any(term in lowered for term in ("confirm", "corrig", "regra", "casa", "principal", "pc2")):
        return 5, 0.88, "core_fact_or_sandro_correction"
    if category in {"pc_runtime", "sandro_core"}:
        return 4, 0.78, "core_identity_or_runtime_context"
    if category == "tooling":
        return 3, 0.72, "tool_usage_or_tool_result"
    if category == "autonomy":
        return 3, 0.74, "autonomy_or_self_improvement_signal"
    if category in {"projects", "agents", "language"}:
        return 3, 0.70, "project_or_system_context"
    if category in {"lore_simulation", "entities"}:
        return 3, 0.68, "lore_or_entity_context_keep_separate"
    if any(term in lowered for term in ("decidi", "decisão", "decisao", "tarefa", "amanhã", "amanha", "lembrar")):
        return 3, 0.65, "decision_or_task"
    if len(text) > 120:
        return 2, 0.55, "useful_but_low_confidence_context"
    return 1, 0.40, "low_signal"


def destination_for(score: int, category: str) -> str:
    if score <= 0:
        return "discard"
    if category == "error":
        return "error_backlog"
    if category == "tooling":
        return "tool_lessons"
    if category == "autonomy":
        return "autonomy_candidate"
    if score == 1:
        return "discard"
    if score == 2:
        return "short_term"
    if score == 3:
        return "medium_term"
    return "long_term_candidate"


def requires_confirmation(category: str, score: int, sensitivity: str) -> bool:
    if score >= 4:
        return True
    if "health_private" in sensitivity or "relationship_private" in sensitivity:
        return True
    if category in {"sandro_core", "bubu_private", "pc_runtime"}:
        return True
    return False


def candidate_from_entry(channel: str, path: Path, index: int, date_key: str, entry: dict[str, Any]) -> dict[str, Any] | None:
    message = message_from_entry(entry)
    if not message:
        return None
    text = sanitize_excerpt(message, max_chars=900)
    metadata = metadata_from_entry(entry)
    category, category_reason = infer_category(text, channel, metadata)
    sensitivity = infer_sensitivity(text, category)
    score, confidence, importance_reason = infer_importance(text, channel, category, metadata)
    if "conflict" in text.lower() or "contradi" in text.lower():
        category = "conflict"
        score = max(score, 3)
        confidence = max(confidence, 0.70)
        importance_reason = "possible_memory_conflict"
    destination = destination_for(score, category)
    reason = category_reason or importance_reason
    return {
        "candidate_id": stable_id(date_key, channel, str(path), str(index), content_hash(text)),
        "date": date_key,
        "source_channel": channel,
        "source_file": str(path),
        "text": text,
        "category": category,
        "sensitivity": sensitivity,
        "importance_score": score,
        "recommended_destination": destination,
        "confidence": round(confidence, 2),
        "reason": reason,
        "requires_sandro_confirmation": requires_confirmation(category, score, sensitivity),
        "status": "proposed",
    }


def build_candidates(date_key: str, transcripts: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for channel, rows in transcripts.items():
        path = transcript_path(channel, date_key)
        for index, entry in enumerate(rows):
            candidate = candidate_from_entry(channel, path, index, date_key, entry)
            if not candidate:
                continue
            digest = content_hash(candidate["text"])
            if digest in seen:
                continue
            seen.add(digest)
            candidates.append(candidate)
    return candidates


def write_jsonl(path: Path, rows: list[dict[str, Any]], *, append: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def write_markdown(path: Path, lines: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def entry_time(entry: dict[str, Any]) -> str:
    return str(entry.get("timestamp") or metadata_from_entry(entry).get("real_timestamp") or "")


def severity_for_error(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ("token", "secret", "security", "permission", "admin", "critical")):
        return "critical"
    if any(term in lowered for term in ("traceback", "exception", "failed", "crash", "erro")):
        return "high"
    if any(term in lowered for term in ("warning", "timeout", "falha")):
        return "medium"
    return "low"


def probable_cause_for_error(text: str) -> str:
    lowered = text.lower()
    if "timeout" in lowered:
        return "timeout_or_slow_dependency"
    if "permission" in lowered or "admin" in lowered:
        return "permission_or_elevation_issue"
    if "not found" in lowered or "no such" in lowered:
        return "missing_file_or_dependency"
    if "ocr" in lowered or "browser" in lowered or "web" in lowered:
        return "ui_or_browser_automation_issue"
    if "vector" in lowered or "chroma" in lowered or "ollama" in lowered:
        return "local_memory_retrieval_dependency"
    return "needs_manual_review"


def write_error_review(date_key: str, transcripts: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]]) -> tuple[Path, list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    for channel, rows in transcripts.items():
        for index, entry in enumerate(rows):
            text = message_from_entry(entry)
            if channel != "errors" and "error" not in text.lower() and "erro" not in text.lower() and "failed" not in text.lower():
                continue
            summary = sanitize_excerpt(text, 500)
            if not summary:
                continue
            severity = severity_for_error(summary)
            errors.append(
                {
                    "error_id": stable_id(date_key, channel, str(index), content_hash(summary)),
                    "date": date_key,
                    "channel": channel,
                    "time": entry_time(entry),
                    "summary": summary,
                    "probable_cause": probable_cause_for_error(summary),
                    "severity": severity,
                    "needs_codex": severity in {"high", "critical"},
                    "needs_sandro": severity == "critical",
                    "suggested_fix": "review_error_cluster_and_create_regression_test" if severity in {"high", "critical"} else "monitor_or_mark_resolved_if_not_repeated",
                    "status": "open" if severity in {"high", "critical"} else "proposed",
                }
            )
    for candidate in candidates:
        if candidate.get("category") == "error" and not any(item["error_id"] == candidate["candidate_id"] for item in errors):
            severity = severity_for_error(candidate["text"])
            errors.append(
                {
                    "error_id": candidate["candidate_id"],
                    "date": date_key,
                    "channel": candidate["source_channel"],
                    "time": "",
                    "summary": candidate["text"],
                    "probable_cause": probable_cause_for_error(candidate["text"]),
                    "severity": severity,
                    "needs_codex": severity in {"high", "critical"},
                    "needs_sandro": severity == "critical",
                    "suggested_fix": "review_error_candidate",
                    "status": "open" if severity in {"high", "critical"} else "proposed",
                }
            )
    lines = [
        f"# Daily Error Review - {date_key}",
        "",
        f"Generated: {now_iso()}",
        "",
        f"- Errors found: {len(errors)}",
        "",
    ]
    if not errors:
        lines.append("No relevant errors found.")
    for item in errors:
        lines.extend(
            [
                f"## {item['error_id']}",
                "",
                f"- Channel: {item['channel']}",
                f"- Time: {item['time'] or 'unknown'}",
                f"- Severity: {item['severity']}",
                f"- Probable cause: {item['probable_cause']}",
                f"- Needs Codex: {item['needs_codex']}",
                f"- Needs Sandro: {item['needs_sandro']}",
                f"- Suggested fix: {item['suggested_fix']}",
                f"- Status: {item['status']}",
                "",
                f"Summary: {item['summary']}",
                "",
            ]
        )
    path = write_markdown(ERROR_REVIEW_DIR / f"{date_key}_error_review.md", lines)
    relevant = [item for item in errors if item["severity"] in {"medium", "high", "critical"}]
    if relevant:
        write_jsonl(ERROR_BACKLOG_PATH, relevant, append=True)
    return path, errors


def write_tool_review(date_key: str, transcripts: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]]) -> tuple[Path, list[dict[str, Any]]]:
    tool_events: list[dict[str, Any]] = []
    for index, entry in enumerate(transcripts.get("tools", [])):
        metadata = metadata_from_entry(entry)
        text = message_from_entry(entry)
        ok = metadata.get("ok")
        status = "ok" if ok is True else "failed_or_unknown" if ok is False or "error" in text.lower() else "observed"
        tool_events.append(
            {
                "tool_event_id": stable_id(date_key, "tools", str(index), content_hash(text)),
                "date": date_key,
                "channel": "tools",
                "tool_name": metadata.get("tool_name") or "unknown_tool",
                "action": metadata.get("action") or "unknown_action",
                "result_summary": sanitize_excerpt(text, 500),
                "status": status,
                "improvement_proposed": status != "ok",
            }
        )
    lines = [
        f"# Daily Tool Review - {date_key}",
        "",
        f"Generated: {now_iso()}",
        "",
        f"- Tool events: {len(tool_events)}",
        f"- Tooling candidates: {sum(1 for item in candidates if item.get('category') == 'tooling')}",
        "",
    ]
    if not tool_events:
        lines.append("No tool events found.")
    for item in tool_events:
        lines.extend(
            [
                f"## {item['tool_event_id']}",
                "",
                f"- Tool: {item['tool_name']}",
                f"- Action: {item['action']}",
                f"- Status: {item['status']}",
                f"- Improvement proposed: {item['improvement_proposed']}",
                "",
                f"Result: {item['result_summary']}",
                "",
            ]
        )
    path = write_markdown(TOOL_REVIEW_DIR / f"{date_key}_tool_review.md", lines)
    lessons = [
        {
            "lesson_id": item["tool_event_id"],
            "date": date_key,
            "tool_name": item["tool_name"],
            "lesson": "tool_event_needs_review" if item["improvement_proposed"] else "tool_event_successful",
            "evidence": item["result_summary"],
            "status": "proposed",
        }
        for item in tool_events
        if item["improvement_proposed"]
    ]
    if lessons:
        write_jsonl(TOOL_LESSONS_PATH, lessons, append=True)
    return path, tool_events


def arsi_candidates_from(candidates: list[dict[str, Any]], errors: list[dict[str, Any]], tools: list[dict[str, Any]], date_key: str) -> list[dict[str, Any]]:
    arsi: list[dict[str, Any]] = []
    for item in errors:
        if item["severity"] in {"high", "critical"}:
            arsi.append(
                {
                    "candidate_id": stable_id("arsi", date_key, item["error_id"]),
                    "date": date_key,
                    "title": f"Investigate recurring/high severity error: {item['probable_cause']}",
                    "candidate_type": "bugfix",
                    "reason": item["summary"],
                    "evidence": item["error_id"],
                    "risk": "medium" if item["severity"] == "high" else "high",
                    "requires_codex": True,
                    "requires_sandro_confirmation": True,
                    "auto_apply": False,
                    "status": "proposed",
                }
            )
    for item in tools:
        if item["improvement_proposed"]:
            arsi.append(
                {
                    "candidate_id": stable_id("arsi_tool", date_key, item["tool_event_id"]),
                    "date": date_key,
                    "title": f"Improve tool reliability: {item['tool_name']}",
                    "candidate_type": "tool_improvement",
                    "reason": item["result_summary"],
                    "evidence": item["tool_event_id"],
                    "risk": "low",
                    "requires_codex": True,
                    "requires_sandro_confirmation": True,
                    "auto_apply": False,
                    "status": "proposed",
                }
            )
    for candidate in candidates:
        if candidate["recommended_destination"] == "autonomy_candidate":
            arsi.append(
                {
                    "candidate_id": stable_id("arsi_memory", date_key, candidate["candidate_id"]),
                    "date": date_key,
                    "title": "Autonomy or memory improvement signal",
                    "candidate_type": "memory_improvement",
                    "reason": candidate["reason"],
                    "evidence": candidate["text"],
                    "risk": "low",
                    "requires_codex": True,
                    "requires_sandro_confirmation": True,
                    "auto_apply": False,
                    "status": "proposed",
                }
            )
    deduped: dict[str, dict[str, Any]] = {}
    for item in arsi:
        deduped[item["candidate_id"]] = item
    return list(deduped.values())


def write_arsi_candidates(date_key: str, arsi: list[dict[str, Any]]) -> Path:
    path = AUTONOMY_DIR / f"{date_key}_arsi_candidates.jsonl"
    write_jsonl(path, arsi)
    if arsi:
        write_jsonl(AUTONOMY_CANDIDATES_PATH, arsi, append=True)
    return path


def group_candidates(candidates: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        grouped[str(candidate.get("recommended_destination") or "discard")].append(candidate)
    return grouped


def write_promotion_plan(date_key: str, candidates: list[dict[str, Any]]) -> tuple[Path, Path, Path, Path]:
    grouped = group_candidates(candidates)
    short = grouped.get("short_term", [])
    medium = grouped.get("medium_term", [])
    long_term = grouped.get("long_term_candidate", [])
    discarded = grouped.get("discard", [])
    pending_path = SHORT_TERM_PENDING_DIR / f"{date_key}_pending.md"
    medium_path = MEDIUM_TERM_CANDIDATES_DIR / f"{date_key}_medium_term_candidates.md"
    long_path = PROMOTION_DIR / f"{date_key}_long_term_candidates.md"
    plan_path = PROMOTION_DIR / f"{date_key}_promotion_plan.md"

    def candidate_lines(items: list[dict[str, Any]]) -> list[str]:
        if not items:
            return ["- None"]
        return [f"- [{item['source_channel']}] score={item['importance_score']} category={item['category']} confirm={item['requires_sandro_confirmation']}: {item['text'][:240]}" for item in items]

    write_markdown(pending_path, [f"# Short-Term Pending - {date_key}", "", *candidate_lines(short)])
    write_markdown(medium_path, [f"# Medium-Term Candidates - {date_key}", "", *candidate_lines(medium)])
    write_markdown(long_path, [f"# Long-Term Candidates - {date_key}", "", "These are candidates only. No stable long-term write was performed.", "", *candidate_lines(long_term)])
    lines = [
        f"# Memory Promotion Plan - {date_key}",
        "",
        f"Generated: {now_iso()}",
        "",
        "No stable long-term memory was written by this rollover.",
        "",
        f"- Short-term proposed: {len(short)}",
        f"- Medium-term proposed: {len(medium)}",
        f"- Long-term candidates: {len(long_term)}",
        f"- Discard/noise: {len(discarded)}",
        f"- Needs Sandro confirmation: {sum(1 for item in candidates if item.get('requires_sandro_confirmation'))}",
        "",
        "## Short-Term",
        "",
        *candidate_lines(short[:25]),
        "",
        "## Medium-Term",
        "",
        *candidate_lines(medium[:25]),
        "",
        "## Long-Term Candidates",
        "",
        *candidate_lines(long_term[:25]),
        "",
        "## Ignored / Low Signal",
        "",
        *candidate_lines(discarded[:20]),
    ]
    write_markdown(plan_path, lines)
    return plan_path, pending_path, medium_path, long_path


def write_rollup(
    date_key: str,
    transcripts: dict[str, list[dict[str, Any]]],
    candidates: list[dict[str, Any]],
    *,
    run_label: str | None,
    forced: bool,
) -> Path:
    counts = {channel: len(rows) for channel, rows in transcripts.items()}
    category_counts = Counter(candidate["category"] for candidate in candidates)
    destination_counts = Counter(candidate["recommended_destination"] for candidate in candidates)
    sensitivity_counts = Counter(candidate["sensitivity"] for candidate in candidates)
    high = [candidate for candidate in candidates if int(candidate.get("importance_score") or 0) >= 4]
    lines = [
        f"# Daily Memory Rollup - {date_key}",
        "",
        f"Generated: {now_iso()}",
        "Mode: deterministic local memory processing. No LLM. No external API. No automatic stable long-term promotion.",
        f"Run label: {run_label or 'daily_rollover'}",
        f"Forced before midnight: {forced}",
        "",
        "## Channels",
        "",
    ]
    lines.extend(f"- {channel}: {count} entries" for channel, count in counts.items())
    lines.extend(
        [
            "",
            "## Candidate Summary",
            "",
            f"- Candidates proposed: {len(candidates)}",
            f"- Categories: {dict(category_counts)}",
            f"- Destinations: {dict(destination_counts)}",
            f"- Sensitivities: {dict(sensitivity_counts)}",
            f"- Needs Sandro confirmation: {sum(1 for item in candidates if item.get('requires_sandro_confirmation'))}",
            "",
            "## High Importance Candidates",
            "",
        ]
    )
    if not high:
        lines.append("No high-importance candidates found.")
    for candidate in high[:30]:
        lines.append(f"- [{candidate['source_channel']}] score={candidate['importance_score']} category={candidate['category']} -> {candidate['recommended_destination']}: {candidate['text'][:260]}")
    return write_markdown(ROLLUP_DIR / f"{date_key}_rollup.md", lines)


def write_dream(
    date_key: str,
    transcripts: dict[str, list[dict[str, Any]]],
    candidates: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    arsi: list[dict[str, Any]],
    *,
    run_label: str | None,
    forced: bool,
) -> Path:
    category_counts = Counter(candidate["category"] for candidate in candidates)
    project_candidates = [item for item in candidates if item["category"] in {"projects", "pc_runtime", "language", "agents"}]
    conflicts = [item for item in candidates if item["category"] == "conflict"]
    lines = [
        f"# Eve Daily Dream / Consolidation - {date_key}",
        "",
        f"Generated: {now_iso()}",
        "This is a practical deterministic consolidation report, not a poetic dream.",
        f"Run label: {run_label or 'daily_rollover'}",
        f"Forced before midnight: {forced}",
        "",
        "## Day Summary",
        "",
        f"- Transcript entries: {sum(len(rows) for rows in transcripts.values())}",
        f"- Memory candidates: {len(candidates)}",
        f"- Error items: {len(errors)}",
        f"- Tool events: {len(tools)}",
        f"- ARSI candidates proposed: {len(arsi)}",
        "",
        "## Memory Patterns",
        "",
    ]
    if category_counts:
        lines.extend(f"- {category}: {count}" for category, count in category_counts.most_common())
    else:
        lines.append("- No strong patterns detected.")
    lines.extend(["", "## Conflicts", ""])
    lines.extend([f"- {item['text'][:240]}" for item in conflicts[:10]] or ["- None detected."])
    lines.extend(["", "## Projects / Runtime That Advanced", ""])
    lines.extend([f"- {item['category']}: {item['text'][:240]}" for item in project_candidates[:15]] or ["- None detected."])
    lines.extend(["", "## Risks", ""])
    if errors:
        lines.extend(f"- {item['severity']}: {item['summary'][:220]}" for item in errors[:10])
    else:
        lines.append("- No daily error risks detected.")
    lines.extend(["", "## Suggestions For Tomorrow", ""])
    if arsi:
        lines.extend(f"- Review ARSI candidate: {item['title']}" for item in arsi[:10])
    else:
        lines.append("- Continue normal memory collection and keep channels alive.")
    lines.extend(["", "## Eve Should Remember Tomorrow", ""])
    lines.extend([f"- {item['text'][:240]}" for item in candidates if item["importance_score"] >= 3][:15] or ["- No medium/high memory candidates today."])
    return write_markdown(DREAM_DIR / f"{date_key}_dream.md", lines)


def chunk_from_file(date_key: str, path: Path, source_type: str, category: str, sensitivity: str, importance: int, index: int) -> dict[str, Any] | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    content = sanitize_excerpt(text, max_chars=2500)
    if not content:
        return None
    return {
        "chunk_id": f"daily-{source_type}-{date_key}-{stable_id(str(path), content_hash(content))}",
        "source_file": path.name,
        "source_path": str(path),
        "source_name": f"{source_type}_{date_key}",
        "source_type": source_type,
        "version": date_key,
        "category": category,
        "sensitivity": sensitivity,
        "importance_hint": importance,
        "chunk_index": index,
        "content": content,
        "content_hash": content_hash(content),
        "imported_at": now_iso(),
    }


def chunks_from_outputs(date_key: str, output_paths: dict[str, Path], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    specs = [
        ("daily_rollup", output_paths["rollup"], "transcripts", "private", 2),
        ("memory_candidates", output_paths["candidates"], "transcripts", "private", 3),
        ("error_review", output_paths["error_review"], "error", "technical_private", 4),
        ("tool_review", output_paths["tool_review"], "tooling", "technical_private", 3),
        ("arsi_candidates", output_paths["arsi"], "autonomy", "technical_private", 3),
        ("promotion_plan", output_paths["promotion_plan"], "transcripts", "private", 3),
        ("dream_report", output_paths["dream"], "eve_identity", "private", 3),
    ]
    for index, (source_type, path, category, sensitivity, importance) in enumerate(specs):
        chunk = chunk_from_file(date_key, path, source_type, category, sensitivity, importance, index)
        if chunk:
            chunks.append(chunk)
    for index, candidate in enumerate(candidates):
        if int(candidate.get("importance_score") or 0) < 2:
            continue
        text = str(candidate.get("text") or "").strip()
        if not text:
            continue
        chunks.append(
            {
                "chunk_id": f"daily-candidate-{date_key}-{candidate['candidate_id']}",
                "source_file": output_paths["candidates"].name,
                "source_path": str(output_paths["candidates"]),
                "source_name": f"daily_candidate_{date_key}",
                "source_type": "daily_candidate",
                "version": date_key,
                "category": candidate.get("category") or "unknown",
                "sensitivity": candidate.get("sensitivity") or "private",
                "importance_hint": int(candidate.get("importance_score") or 2),
                "chunk_index": index,
                "content": text,
                "content_hash": content_hash(text),
                "imported_at": now_iso(),
                "recommended_destination": candidate.get("recommended_destination"),
                "status": candidate.get("status"),
            }
        )
    return chunks


def update_vector_incremental(chunks_path: Path) -> dict[str, Any]:
    script = EVE_ROOT / "scripts" / "update_vector_memory_incremental.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--input", str(chunks_path)],
        cwd=str(EVE_ROOT),
        capture_output=True,
        text=True,
        timeout=900,
    )
    if completed.returncode != 0:
        return {"ok": False, "stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]}
    try:
        return json.loads(completed.stdout[completed.stdout.find("{") : completed.stdout.rfind("}") + 1])
    except Exception:
        return {"ok": False, "stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:], "error": "could not parse vector update json"}


def run_continual_learning(date_key: str) -> dict[str, Any]:
    scripts = [
        ("analysis", EVE_ROOT / "scripts" / "analyze_daily_experience.py"),
        ("lessons", EVE_ROOT / "scripts" / "update_lessons_learned.py"),
        ("improvements", EVE_ROOT / "scripts" / "propose_self_improvements.py"),
    ]
    results: dict[str, Any] = {}
    for name, script in scripts:
        if not script.exists():
            results[name] = {"ok": False, "error": f"missing script: {script}"}
            continue
        completed = subprocess.run(
            [sys.executable, str(script), "--date", date_key],
            cwd=str(EVE_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        try:
            start = completed.stdout.find("{")
            payload = json.loads(completed.stdout[start:].strip()) if start >= 0 else {}
        except json.JSONDecodeError:
            payload = {}
        payload.update(
            {
                "ok": completed.returncode == 0 and bool(payload.get("ok", True)),
                "returncode": completed.returncode,
                "stdout_tail": completed.stdout[-1200:],
                "stderr_tail": completed.stderr[-1200:],
            }
        )
        results[name] = payload
    results["ok"] = all(item.get("ok") for item in results.values() if isinstance(item, dict))
    return results


def write_memory_day_override(previous_day: str, active_day: str, reason: str) -> Path:
    SESSION_STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "enabled": True,
        "active_memory_day": active_day,
        "previous_memory_day": previous_day,
        "reason": reason,
        "created_at": now_iso(),
        "expires_mode": "manual_or_next_midnight",
    }
    MEMORY_DAY_OVERRIDE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return MEMORY_DAY_OVERRIDE_PATH


def compact_list(items: list[str], limit: int = 4) -> list[str]:
    clean = [sanitize_excerpt(item, 180) for item in items if str(item or "").strip()]
    return clean[:limit] or ["None detected."]


def build_session_handoff(
    date_key: str,
    next_date_key: str,
    transcripts: dict[str, list[dict[str, Any]]],
    candidates: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    arsi: list[dict[str, Any]],
    output_paths: dict[str, Path],
) -> Path:
    important = sorted(candidates, key=lambda item: (int(item.get("importance_score") or 0), float(item.get("confidence") or 0)), reverse=True)
    topics = [f"{item['category']}: {item['text']}" for item in important]
    tasks = [item["text"] for item in candidates if any(term in item["text"].lower() for term in ("tarefa", "amanha", "amanhã", "próximo", "proximo", "instalar", "testar", "corrigir"))]
    decisions = [item["text"] for item in candidates if any(term in item["text"].lower() for term in ("confirm", "decidi", "decisão", "decisao", "ficou", "instalada", "ready"))]
    warnings = [f"{item['severity']}: {item['summary']}" for item in errors[:4]]
    last_messages: list[str] = []
    for channel in ("terminal", "telegram", "webui"):
        for entry in transcripts.get(channel, [])[-2:]:
            speaker = entry.get("speaker") or "unknown"
            last_messages.append(f"{channel}/{speaker}: {message_from_entry(entry)}")
    next_steps = [item["title"] for item in arsi[:2]] or tasks[:2] or ["Continue from the latest memory rollover and verify the next user request against the compact handoff."]
    lines = [
        "# Eve Session Handoff",
        "",
        "## Previous session",
        f"- Session ID: {date_key}_main",
        f"- Memory day: {date_key}",
        f"- Closed at: {now_iso()}",
        "",
        "## Current focus",
        "Daily memory processing, rollover continuity, compact handoff, and keeping Eve's PC2 runtime coherent without carrying the full day transcript.",
        "",
        "## Last active topics",
        *[f"- {item}" for item in compact_list(topics, 5)],
        "",
        "## Open tasks",
        *[f"- {item}" for item in compact_list(tasks, 4)],
        "",
        "## Decisions made",
        *[f"- {item}" for item in compact_list(decisions, 4)],
        "",
        "## Important warnings",
        *[f"- {item}" for item in compact_list(warnings, 4)],
        "",
        "## Next recommended step",
        *[f"- {item}" for item in compact_list(next_steps, 2)],
        "",
        "## Last messages summary",
        *[f"- {item}" for item in compact_list(last_messages, 6)],
        "",
        "## Memory links",
        f"- rollup: {output_paths['rollup']}",
        f"- dream: {output_paths['dream']}",
        f"- candidates: {output_paths['candidates']}",
        f"- error review: {output_paths['error_review']}",
        f"- tool review: {output_paths['tool_review']}",
        f"- promotion plan: {output_paths['promotion_plan']}",
    ]
    text = "\n".join(lines).strip()
    if len(text) > 3900:
        text = text[:3800].rstrip() + "\n\n[handoff truncated to absolute limit]"
    path = SESSION_HANDOFF_DIR / f"{date_key}_to_{next_date_key}_handoff.md"
    write_markdown(path, text.splitlines())
    LATEST_HANDOFF_PATH.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def close_session(
    date_key: str,
    next_date_key: str,
    handoff_path: Path,
    transcripts: dict[str, list[dict[str, Any]]],
    output_paths: dict[str, Path],
    vector_chunks_added: int,
) -> Path:
    payload = {
        "session_id": f"{date_key}_main",
        "memory_day": date_key,
        "closed_at": now_iso(),
        "rollup_path": str(output_paths["rollup"]),
        "handoff_path": str(handoff_path),
        "channels_processed": [channel for channel, rows in transcripts.items() if rows],
        "transcript_files": [str(transcript_path(channel, date_key)) for channel, rows in transcripts.items() if rows],
        "vector_chunks_added": int(vector_chunks_added),
        "status": "closed",
        "next_session_id": f"{next_date_key}_main",
    }
    path = SESSION_ARCHIVE_DIR / f"{date_key}_session_close.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def open_new_session(date_key: str, next_date_key: str, handoff_path: Path) -> Path:
    payload = {
        "session_id": f"{next_date_key}_main",
        "memory_day": next_date_key,
        "started_at": now_iso(),
        "channels": ["terminal", "telegram", "webui"],
        "handoff_loaded": True,
        "previous_session_id": f"{date_key}_main",
        "handoff_path": str(handoff_path),
        "latest_handoff_path": str(LATEST_HANDOFF_PATH),
        "status": "active",
    }
    CURRENT_SESSION_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return CURRENT_SESSION_PATH


def run(
    date: datetime,
    *,
    force: bool = False,
    close_current_day: bool = False,
    advance_memory_day: bool = False,
    test_run_label: str | None = None,
    run_continual_learning_analysis: bool = True,
) -> dict[str, Any]:
    ensure_dirs()
    date_key = date.strftime("%Y-%m-%d")
    transcripts = load_transcripts(date_key)
    candidates = build_candidates(date_key, transcripts)
    classifications_path = CLASSIFICATIONS_DIR / f"{date_key}_memory_candidates.jsonl"
    write_jsonl(classifications_path, candidates)
    error_review_path, errors = write_error_review(date_key, transcripts, candidates)
    tool_review_path, tools = write_tool_review(date_key, transcripts, candidates)
    arsi = arsi_candidates_from(candidates, errors, tools, date_key)
    arsi_path = write_arsi_candidates(date_key, arsi)
    promotion_plan_path, short_path, medium_path, long_path = write_promotion_plan(date_key, candidates)
    rollup_path = write_rollup(date_key, transcripts, candidates, run_label=test_run_label, forced=force)
    dream_path = write_dream(date_key, transcripts, candidates, errors, tools, arsi, run_label=test_run_label, forced=force)
    output_paths = {
        "rollup": rollup_path,
        "candidates": classifications_path,
        "error_review": error_review_path,
        "tool_review": tool_review_path,
        "arsi": arsi_path,
        "promotion_plan": promotion_plan_path,
        "dream": dream_path,
    }
    chunks = chunks_from_outputs(date_key, output_paths, candidates)
    chunks_path = CHUNKS_DIR / f"{date_key}_daily_chunks.jsonl"
    write_jsonl(chunks_path, chunks)
    vector_result = update_vector_incremental(chunks_path) if chunks else {"ok": True, "chunks_seen": 0, "chunks_indexed": 0}
    next_date_key = (date + timedelta(days=1)).strftime("%Y-%m-%d")
    handoff_path = build_session_handoff(date_key, next_date_key, transcripts, candidates, errors, arsi, output_paths)
    session_archive_path = close_session(
        date_key,
        next_date_key,
        handoff_path,
        transcripts,
        output_paths,
        int(vector_result.get("chunks_indexed") or 0),
    )
    current_session_path = open_new_session(date_key, next_date_key, handoff_path)
    override_path = None
    active_memory_day = date_key
    if close_current_day and advance_memory_day:
        active_memory_day = next_date_key
        override_path = str(write_memory_day_override(date_key, active_memory_day, test_run_label or "forced_rollover"))
    continual_learning = run_continual_learning(date_key) if run_continual_learning_analysis else {"ok": True, "skipped": True}
    return {
        "ok": bool(vector_result.get("ok")),
        "date": date_key,
        "forced": force,
        "closed_memory_day": date_key if close_current_day else None,
        "active_memory_day": active_memory_day,
        "memory_day_override": override_path,
        "test_run_label": test_run_label,
        "rollup": str(rollup_path),
        "candidates": str(classifications_path),
        "error_review": str(error_review_path),
        "tool_review": str(tool_review_path),
        "arsi_candidates": str(arsi_path),
        "promotion_plan": str(promotion_plan_path),
        "short_term_pending": str(short_path),
        "medium_term_candidates": str(medium_path),
        "long_term_candidates": str(long_path),
        "dream": str(dream_path),
        "session_handoff": str(handoff_path),
        "latest_handoff": str(LATEST_HANDOFF_PATH),
        "session_archive": str(session_archive_path),
        "current_session": str(current_session_path),
        "chunks": str(chunks_path),
        "candidate_count": len(candidates),
        "error_count": len(errors),
        "tool_event_count": len(tools),
        "arsi_candidate_count": len(arsi),
        "chunk_count": len(chunks),
        "vector_update": vector_result,
        "continual_learning": continual_learning,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Eve safe daily memory rollover with richer local processing and incremental vector update.")
    parser.add_argument("--date", help="Date in YYYY-MM-DD. Defaults to today, or yesterday when run shortly after midnight.")
    parser.add_argument("--force", action="store_true", help="Allow a controlled rollover before midnight.")
    parser.add_argument("--close-current-day", action="store_true", help="Mark the selected memory day as closed in the output metadata.")
    parser.add_argument("--advance-memory-day", action="store_true", help="Create a memory-day override pointing new transcripts at the next day.")
    parser.add_argument("--test-run-label", default=None, help="Optional label for controlled/manual test runs.")
    parser.add_argument("--skip-continual-learning", action="store_true", help="Skip continual learning proposal generation.")
    args = parser.parse_args()
    date = parse_date(args.date) if args.date else default_rollover_date()
    result = run(
        date,
        force=args.force,
        close_current_day=args.close_current_day,
        advance_memory_day=args.advance_memory_day,
        test_run_label=args.test_run_label,
        run_continual_learning_analysis=not args.skip_continual_learning,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

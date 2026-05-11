from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autonomy.capability_roadmap import TARGET_CAPABILITY_SCORE, append_capability_review_history, capability_audit, ensure_capability_review_schedule, write_capability_audit
from core.paths import LOGS_DIR, MEMORY_DIR, ensure_project_dirs
from memory.daily_transcripts import ensure_daily_transcript_files
from research.daily_research_plan import ensure_daily_research_pipeline_schedule
from research.interest_evolution import ensure_interest_evolution_schedule


HARNESS_CONTROLS: dict[int, list[str]] = {
    1: ["admin policy is gated", "admin actions have a log target", "admin command path is explicit"],
    2: ["daily transcript files exist", "chat/tools/actions/errors channels are separated", "runtime can append events"],
    3: ["capability review is scheduled", "daemon calls the harness", "history is appended"],
    4: ["short/medium/long memory directories exist", "promotion outputs are auditable", "context retrieval has a stable entrypoint"],
    5: ["semantic vector directory exists", "vector rebuild is callable", "prefetch is exposed as a tool"],
    6: ["dream report directory exists", "dream cycle can queue lab ideas", "memory decisions are written to reports"],
    7: ["awareness engine is callable", "screen/window tools are present", "tool results require verification"],
    8: ["personality memory exists", "interest evolution schedule exists", "candidate preferences are dated"],
    9: ["lab candidate directory exists", "candidate creation API exists", "reports/queue directories exist"],
    10: ["error transcript exists", "error memory exists", "terminal/tool transcript exists"],
    11: ["daily research pipeline schedule exists", "technology watcher exists", "frontier labs/open-source/papers are tracked"],
    12: ["research-to-lab target exists", "candidate improvement path exists", "daily research prompt includes lab decision"],
    13: ["world daily target exists", "technology daily target exists", "personality daily target exists"],
    14: ["autonomy cycle exists", "verified update path exists", "improvements require tests before core changes"],
    15: ["browser control exists", "keyboard/mouse control exists", "screenshots/OCR are available"],
    16: ["recursive self-improvement policy exists", "backup path exists", "verified update requires rollback/test discipline"],
    17: ["daemon heartbeat exists or can be written", "cron jobs exist", "autonomous executor is bounded and auditable"],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _append_jsonl(path: Path, row: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _point_status(point: dict[str, Any], *, target: float) -> dict[str, Any]:
    score = float(point.get("score_10") or 0.0)
    gaps = list(point.get("goal_gaps") or [])
    controls = HARNESS_CONTROLS.get(int(point["id"]), [])
    if score < target:
        gaps.append(f"codex hardening required: score below {target}/10")
    return {
        "id": point["id"],
        "title": point["title"],
        "score_10": score,
        "target_score": target,
        "meets_target": score >= target,
        "maturity": point.get("maturity"),
        "controls": controls,
        "evidence": point.get("evidence") or [],
        "habit_evidence": point.get("habit_evidence") or [],
        "improvement_evidence": point.get("improvement_evidence") or [],
        "missing_paths": point.get("missing_paths") or [],
        "gaps": gaps,
    }


def _format_report(result: dict[str, Any]) -> str:
    lines = [
        "# Eve 17-Point Capability Goal Harness",
        "",
        f"Timestamp: {result['timestamp']}",
        f"Target: {result['target_score']}/10",
        f"All points meet target: {result['all_meet_target']}",
        f"Points below target: {len(result['points_below_target'])}",
        "",
        "## Operational Setup",
        f"- Transcripts: {result['setup']['transcripts']}",
        f"- Capability schedule: {result['setup']['capability_schedule']}",
        f"- Interest schedule: {result['setup']['interest_schedule']}",
        f"- Daily research schedule: {result['setup']['daily_research_schedule']}",
        f"- Roadmap path: {result['setup']['roadmap_path']}",
        f"- History path: {result['setup']['history_path']}",
        "",
    ]
    for point in result["points"]:
        lines.extend(
            [
                f"## {point['id']}. {point['title']}",
                f"- Score: {point['score_10']} / {point['target_score']} | Meets target: {point['meets_target']}",
                f"- Maturity: {point['maturity']}",
                f"- Controls: {', '.join(point['controls']) or 'none'}",
                f"- Evidence: {', '.join(point['evidence']) or 'none'}",
                f"- Habit evidence: {', '.join(point['habit_evidence']) or 'none'}",
                f"- Improvement evidence: {', '.join(point['improvement_evidence']) or 'none'}",
                f"- Missing paths: {', '.join(point['missing_paths']) or 'none'}",
                f"- Gaps for Codex: {', '.join(point['gaps']) or 'none'}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def run_capability_goal_harness(
    *,
    target_score: float = TARGET_CAPABILITY_SCORE,
    ensure_schedules: bool = True,
    write_report: bool = True,
) -> dict[str, Any]:
    """Run the Codex-facing harness for Sandro's 17-point Eve contract.

    This function prepares evidence and schedules, then reports gaps for Codex
    work. It deliberately does not apply self-modifying changes.
    """

    ensure_project_dirs()
    transcripts = ensure_daily_transcript_files()
    roadmap_path = write_capability_audit()
    history_path = append_capability_review_history()
    capability_schedule = ensure_capability_review_schedule(schedule="6h") if ensure_schedules else None
    interest_schedule = ensure_interest_evolution_schedule(schedule="24h") if ensure_schedules else None
    daily_research_schedule = ensure_daily_research_pipeline_schedule(schedule="24h") if ensure_schedules else None

    audit = capability_audit()
    points = [_point_status(point, target=target_score) for point in audit["points"]]
    below = [point for point in points if not point["meets_target"]]
    result = {
        "timestamp": _now_iso(),
        "target_score": target_score,
        "all_meet_target": not below,
        "points_below_target": below,
        "summary": audit["summary"],
        "setup": {
            "transcripts": transcripts,
            "capability_schedule": capability_schedule,
            "interest_schedule": interest_schedule,
            "daily_research_schedule": daily_research_schedule,
            "roadmap_path": str(roadmap_path),
            "history_path": str(history_path),
        },
        "points": points,
        "policy": "Codex hardens the codebase; Eve may report gaps but does not self-modify here.",
    }

    log_path = _append_jsonl(LOGS_DIR / "autonomy" / "capability_goal_harness.jsonl", result)
    result["log_path"] = str(log_path)
    if write_report:
        report_path = MEMORY_DIR / "medium_term" / "eve_17_point_goal_harness.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(_format_report(result), encoding="utf-8")
        result["report_path"] = str(report_path)
    return result

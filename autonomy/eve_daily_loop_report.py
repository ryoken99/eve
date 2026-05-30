from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from core.paths import LOGS_DIR, ensure_project_dirs


def _safe_text(value: Any, *, max_chars: int = 3000) -> str:
    text = str(value)
    if len(text) > max_chars:
        return text[:max_chars] + "\n... [truncated]"
    return text


def _step_map(loop_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(step.get("name")): step for step in loop_result.get("steps", [])}


def _step_section(title: str, step: dict[str, Any] | None) -> list[str]:
    lines = [f"## {title}", ""]
    if not step:
        lines.extend(["- Status: missing", ""])
        return lines
    lines.append(f"- Status: {'ok' if step.get('ok') else 'failed'}")
    if step.get("error"):
        lines.append(f"- Error: `{step.get('error')}`")
    result = step.get("result")
    if result not in (None, ""):
        lines.extend(["", "```text", _safe_text(result), "```"])
    lines.append("")
    return lines


def write_daily_loop_report(loop_result: dict[str, Any]) -> Path:
    """Write the markdown report for a daily loop run."""

    ensure_project_dirs()
    now = datetime.now()
    report_dir = LOGS_DIR / "autonomy" / "daily_loop"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{now.strftime('%Y-%m-%d')}.md"
    steps = _step_map(loop_result)

    capability = steps.get("capability_audit", {}).get("result") or {}
    metrics = steps.get("evolution_metrics", {}).get("result") or {}
    weakest = []
    if isinstance(capability, dict):
        weakest = capability.get("weakest") or []
    if isinstance(metrics, dict) and not weakest:
        weakest = metrics.get("weakest_capability_points") or []

    message = _message_for_sandro(loop_result, metrics, weakest)

    lines = [
        f"# Eve Daily Loop Report - {now.strftime('%Y-%m-%d')}",
        "",
        f"Generated: {now.isoformat(timespec='seconds')}",
        f"Cycle: `{loop_result.get('cycle_name')}`",
        f"Dry run: `{loop_result.get('dry_run')}`",
        f"Overall ok: `{loop_result.get('ok')}`",
        "",
    ]

    lines.extend(_step_section("Awareness", steps.get("awareness")))
    lines.extend(_step_section("Transcripts", steps.get("transcripts")))
    lines.extend(_step_section("Diary Consolidation", steps.get("diary_consolidation")))
    lines.extend(_step_section("Dream / Memory Review", steps.get("dream_memory_review")))
    lines.extend(_step_section("Error Review", steps.get("error_review")))
    lines.extend(_step_section("Research Inbox", steps.get("research_inbox")))
    lines.extend(_step_section("Lab Candidates", steps.get("lab_candidates")))
    lines.extend(_step_section("Improvement Planner", steps.get("improvement_plan")))
    lines.extend(_step_section("17-Point Capability Audit", steps.get("capability_audit")))
    lines.extend(_step_section("Evolution Metrics", steps.get("evolution_metrics")))

    lines.extend(
        [
            "## Next Recommended Actions",
            "",
            *[f"- {item}" for item in loop_result.get("next_recommended_actions", [])],
            "",
            "## Message To Sandro",
            "",
            message,
            "",
        ]
    )

    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write("\n---\n\n")
    return path


def _message_for_sandro(loop_result: dict[str, Any], metrics: Any, weakest: Any) -> str:
    failed = [step for step in loop_result.get("steps", []) if not step.get("ok")]
    if isinstance(metrics, dict):
        cycles = metrics.get("autonomy_cycles_today", "?")
        score = metrics.get("capability_average_score", "?")
    else:
        cycles = "?"
        score = "?"
    weakest_text = ""
    if weakest:
        names = []
        for item in weakest[:3]:
            if isinstance(item, dict):
                names.append(str(item.get("title") or item.get("id") or item))
            else:
                names.append(str(item))
        weakest_text = " Weakest focus: " + ", ".join(names) + "."
    if failed:
        return (
            f"Sandro, corri o ciclo `{loop_result.get('cycle_name')}` em modo "
            f"{'dry-run' if loop_result.get('dry_run') else 'real'}; {len(failed)} etapa(s) falharam "
            f"mas o ciclo continuou. Autonomy cycles today: {cycles}. Capability score: {score}.{weakest_text}"
        )
    return (
        f"Sandro, corri o ciclo `{loop_result.get('cycle_name')}` e todas as etapas principais passaram. "
        f"Autonomy cycles today: {cycles}. Capability score: {score}.{weakest_text}"
    )

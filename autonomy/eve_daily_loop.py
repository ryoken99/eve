from __future__ import annotations

import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from autonomy.capability_roadmap import capability_audit, write_capability_audit
from autonomy.cron_manager import add_cron_job, list_cron_jobs
from autonomy.eve_daily_loop_report import write_daily_loop_report
from core.awareness_engine import collect_awareness
from core.evolution_metrics import collect_evolution_metrics, write_evolution_metrics_report
from core.paths import EVE_ROOT, LAB_DIR, LOGS_DIR, MEMORY_DIR, ensure_project_dirs
from dream.diary_consolidator import consolidate
from dream.dream_cycle import run_dream_cycle
from lab.lab_manager import create_lab_candidate
from memory.daily_transcripts import ensure_daily_transcript_files
from memory.diary_manager import today_key
from memory.errors.error_memory import recent_errors
from self_improvement.improvement_planner import plan_autonomous_system_improvements


DAILY_LOOP_JOB_NAME = "Eve Daily Metabolism Loop"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_step(name: str, func: Callable[[], Any]) -> dict[str, Any]:
    try:
        result = func()
        return {"name": name, "ok": True, "result": result, "error": None}
    except Exception as exc:
        return {
            "name": name,
            "ok": False,
            "result": None,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=6),
        }


def _paths_to_strings(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _paths_to_strings(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_paths_to_strings(item) for item in value]
    return value


def _collect_research_inbox_summary(max_items: int) -> dict[str, Any]:
    try:
        from research.research_inbox import summarize_research_inbox  # type: ignore

        return summarize_research_inbox(max_items=max_items)
    except ModuleNotFoundError as exc:
        if exc.name != "research.research_inbox":
            raise
    except ImportError:
        pass

    candidates = []
    for root in (MEMORY_DIR / "technology", MEMORY_DIR / "world", MEMORY_DIR / "personality"):
        if not root.exists():
            continue
        for path in sorted(root.rglob("*"), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True):
            if path.is_file() and path.suffix.lower() in {".md", ".json", ".jsonl", ".txt"}:
                candidates.append(str(path))
            if len(candidates) >= max_items:
                break
        if len(candidates) >= max_items:
            break
    return {"ok": True, "source": "fallback_filesystem_scan", "items": candidates, "count": len(candidates)}


def _route_research_items(max_items: int, *, dry_run: bool) -> dict[str, Any]:
    summary = _collect_research_inbox_summary(max_items=max_items)
    routed = {
        "world_learning": [],
        "technology_learning": [],
        "personality_learning": [],
        "lab_candidates": [],
        "dry_run": dry_run,
        "source_summary": summary,
    }
    items = summary.get("items") if isinstance(summary, dict) else []
    for raw in list(items or [])[:max_items]:
        text = str(raw)
        lowered = text.lower()
        if any(token in lowered for token in ("technology", "tech", "ai", "paper", "openai", "anthropic", "model")):
            routed["technology_learning"].append(text)
        elif any(token in lowered for token in ("personality", "interest", "preference", "gosto")):
            routed["personality_learning"].append(text)
        else:
            routed["world_learning"].append(text)
    return routed


def _create_daily_lab_candidates(max_lab_candidates: int, *, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {"dry_run": True, "created": [], "planned": min(max_lab_candidates, 1)}
    created = []
    title = f"daily_loop_quality_{datetime.now().strftime('%Y%m%d')}"
    result = create_lab_candidate(
        title,
        "Test whether the Eve daily metabolism loop improves evidence quality and reduces missed autonomous follow-up.",
        source="eve_daily_loop",
        point_id=17,
        risk="low",
        expected_metric="loop_report_completeness",
    )
    created.append(result)
    return {"dry_run": False, "created": created[:max_lab_candidates], "count": len(created[:max_lab_candidates])}


def run_eve_daily_loop(
    cycle_name: str = "daily",
    dry_run: bool = False,
    max_research_items: int = 5,
    max_lab_candidates: int = 3,
    max_improvement_candidates: int = 3,
) -> dict[str, Any]:
    """Run Eve's central metabolism loop.

    Each step is isolated. Failures are recorded in the returned `steps` list,
    and later steps still run.
    """

    ensure_project_dirs()
    started_at = _now_iso()
    steps: list[dict[str, Any]] = []

    steps.append(_run_step("awareness", lambda: collect_awareness()))
    steps.append(_run_step("transcripts", lambda: ensure_daily_transcript_files()))
    steps.append(_run_step("diary_consolidation", lambda: {"summary": str(consolidate(today_key()))}))
    steps.append(_run_step("dream_memory_review", lambda: _paths_to_strings(run_dream_cycle(today_key()))))
    steps.append(_run_step("error_review", lambda: {"recent_errors": recent_errors(limit=20), "count": len(recent_errors(limit=20))}))
    steps.append(_run_step("research_inbox", lambda: _collect_research_inbox_summary(max_research_items)))
    steps.append(_run_step("research_routing", lambda: _route_research_items(max_research_items, dry_run=dry_run)))
    steps.append(_run_step("lab_candidates", lambda: _create_daily_lab_candidates(max_lab_candidates, dry_run=dry_run)))
    steps.append(
        _run_step(
            "improvement_plan",
            lambda: plan_autonomous_system_improvements(max_items=max_improvement_candidates),
        )
    )
    steps.append(_run_step("capability_audit", lambda: {"audit": capability_audit(), "path": str(write_capability_audit())}))
    steps.append(_run_step("evolution_metrics", lambda: {**collect_evolution_metrics(), "report": str(write_evolution_metrics_report())}))

    finished_at = _now_iso()
    result: dict[str, Any] = {
        "ok": all(step.get("ok") for step in steps),
        "cycle_name": cycle_name,
        "started_at": started_at,
        "finished_at": finished_at,
        "dry_run": dry_run,
        "steps": steps,
        "reports": {"daily_loop_report": None, "capability_audit": None},
        "next_recommended_actions": _next_actions(steps),
    }
    report_path = write_daily_loop_report(result)
    capability_step = next((step for step in steps if step["name"] == "capability_audit"), None)
    capability_path = None
    if capability_step and isinstance(capability_step.get("result"), dict):
        capability_path = capability_step["result"].get("path")
    result["reports"] = {"daily_loop_report": str(report_path), "capability_audit": capability_path}
    return result


def _next_actions(steps: list[dict[str, Any]]) -> list[str]:
    actions = []
    failed = [step for step in steps if not step.get("ok")]
    if failed:
        actions.append("Review failed daily loop steps and turn repeated failures into lab candidates.")
    if any(step["name"] == "research_inbox" and step.get("ok") for step in steps):
        actions.append("Connect Codex 2 research inbox outputs directly to research_routing.")
    actions.append("Keep PC1 as builder/dev and run this loop in dry_run before scheduling on PC2.")
    return actions


def ensure_eve_daily_loop_schedule(schedule: str = "6h") -> dict[str, Any]:
    ensure_project_dirs()
    try:
        existing = [job for job in list_cron_jobs() if job.get("name") == DAILY_LOOP_JOB_NAME]
        if existing:
            return {"ok": True, "status": "exists", "job": existing[0]}
        command = (
            f"Set-Location {EVE_ROOT}; "
            "python -c \"from autonomy.eve_daily_loop import run_eve_daily_loop; "
            "print(run_eve_daily_loop(cycle_name='scheduled', dry_run=False))\""
        )
        job = add_cron_job(DAILY_LOOP_JOB_NAME, schedule, command, enabled=True)
        return {"ok": True, "status": "created", "job": job}
    except Exception as exc:
        plan_dir = LOGS_DIR / "autonomy" / "daily_loop"
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan = plan_dir / "schedule_plan.md"
        plan.write_text(
            "\n".join(
                [
                    "# Eve Daily Loop Schedule Plan",
                    "",
                    f"Requested schedule: `{schedule}`",
                    f"Could not create cron job: `{type(exc).__name__}: {exc}`",
                    "",
                    "Manual command:",
                    "",
                    "```powershell",
                    "python -c \"from autonomy.eve_daily_loop import run_eve_daily_loop; print(run_eve_daily_loop(dry_run=True))\"",
                    "```",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return {"ok": False, "status": "plan_written", "error": f"{type(exc).__name__}: {exc}", "plan": str(plan)}

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from core.paths import EVE_ROOT, LOGS_DIR, STATE_DIR, ensure_project_dirs
from security.audit_log import log_event
from autonomy.cron_manager import add_prompt_job
from tools.windows_scheduler import create_once_task
from tools.x_scheduler import target_datetime_for_time


RESEARCH_JOBS_DIR = STATE_DIR / "research_jobs"


def _safe_task_fragment(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip()).strip("_")
    return cleaned[:40] or "research"


def build_web_research_task_command(job_path: str | Path) -> str:
    runner = EVE_ROOT / "scripts" / "run_web_research_job.py"
    log_dir = LOGS_DIR / "scheduled_tasks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{Path(job_path).stem}.log"
    return (
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
        f"\"Set-Location -LiteralPath '{EVE_ROOT}'; "
        f"& '{sys.executable}' '{runner}' --job '{Path(job_path)}' *> '{log_path}'\""
    )


def write_web_research_job(query: str, scheduled_for: datetime, *, max_pages: int = 8) -> Path:
    ensure_project_dirs()
    RESEARCH_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    job_id = f"web_research_{scheduled_for.strftime('%Y%m%d_%H%M')}_{_safe_task_fragment(query)}"
    path = RESEARCH_JOBS_DIR / f"{job_id}.json"
    payload = {
        "id": job_id,
        "status": "scheduled",
        "query": query,
        "max_pages": int(max_pages),
        "open_visible_browser": True,
        "scheduled_for": scheduled_for.isoformat(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "result": None,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def update_web_research_job(path: str | Path, **updates) -> dict:
    job_path = Path(path)
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    payload.update(updates)
    payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
    job_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def log_web_research_event(event: str, payload: dict) -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "web_research_jobs.jsonl"
    row = {"timestamp": datetime.now().isoformat(timespec="seconds"), "event": event, **payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _create_interactive_task(create_task_func, name: str, time_hhmm: str, date_ddmmyyyy: str, command: str) -> dict:
    try:
        return create_task_func(name, time_hhmm, date_ddmmyyyy, command, interactive=True)
    except TypeError:
        return create_task_func(name, time_hhmm, date_ddmmyyyy, command)


def build_web_research_execution_prompt(query: str, *, max_pages: int = 8, job_path: str | Path | None = None) -> str:
    job_note = f"\nJob local: {job_path}" if job_path else ""
    return (
        "Executa agora esta pesquisa agendada pelo cron interno da Eve.\n"
        "Nao reagendes. Usa a ferramenta web_research_report, abre o Chrome/perfil Eve se for preciso, usa varias fontes, "
        "fecha o separador do browser no fim e responde ao Sandro com um resumo curto.\n"
        f"Query: {query}\nMax pages: {int(max_pages)}{job_note}"
    )


def schedule_web_research_report(
    query: str,
    time_hhmm: str,
    *,
    now: datetime | None = None,
    max_pages: int = 8,
    create_task_func=create_once_task,
    create_prompt_func=add_prompt_job,
) -> dict:
    query = query.strip()
    if not query:
        return {"status": "needs_confirmation", "reason": "Research query is empty."}
    target, note = target_datetime_for_time(time_hhmm, now=now)
    job_path = write_web_research_job(query, target, max_pages=max_pages)
    prompt = build_web_research_execution_prompt(query, max_pages=max_pages, job_path=job_path)
    task_fragment = f"Web_Research_{target.strftime('%Y%m%d_%H%M')}_{_safe_task_fragment(query)}"
    cron_job = create_prompt_func(
        task_fragment,
        target,
        prompt,
        speaker="sandro",
    )
    status = "scheduled" if cron_job.get("id") else "failed"
    update_web_research_job(job_path, status=status, cron_job=cron_job, task_name=cron_job.get("id") or f"Eve_{task_fragment}", note=note)
    result = {
        "status": status,
        "task_name": cron_job.get("id") or f"Eve_{task_fragment}",
        "scheduled_for": target.isoformat(),
        "job_path": str(job_path),
        "query": query,
        "note": note,
        "cron_job": cron_job,
        "execution_prompt": prompt,
        "task_result": {"cron_job": cron_job},
    }
    log_event("web_research_scheduled", result)
    log_web_research_event("scheduled", result)
    return result

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from core.paths import EVE_ROOT, STATE_DIR, ensure_project_dirs
from security.audit_log import log_event


CRON_PATH = STATE_DIR / "cron_jobs.json"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _load() -> list[dict[str, Any]]:
    ensure_project_dirs()
    if not CRON_PATH.exists():
        return []
    try:
        return json.loads(CRON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(jobs: list[dict[str, Any]]) -> Path:
    ensure_project_dirs()
    CRON_PATH.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8")
    return CRON_PATH


def _next_run(schedule: str, *, base: datetime | None = None) -> str:
    base = base or now_utc()
    text = schedule.strip().lower()
    if text.endswith("m") and text[:-1].isdigit():
        return (base + timedelta(minutes=int(text[:-1]))).isoformat().replace("+00:00", "Z")
    if text.endswith("h") and text[:-1].isdigit():
        return (base + timedelta(hours=int(text[:-1]))).isoformat().replace("+00:00", "Z")
    if text.endswith("d") and text[:-1].isdigit():
        return (base + timedelta(days=int(text[:-1]))).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(text.replace("z", "+00:00"))
        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return (base + timedelta(hours=24)).isoformat().replace("+00:00", "Z")


def add_cron_job(name: str, schedule: str, command: str, *, enabled: bool = True) -> dict[str, Any]:
    jobs = _load()
    job = {
        "id": f"cron_{uuid.uuid4().hex[:10]}",
        "name": name,
        "schedule": schedule,
        "command": command,
        "enabled": enabled,
        "created_at": now_utc().isoformat().replace("+00:00", "Z"),
        "last_run": None,
        "next_run": _next_run(schedule),
        "run_count": 0,
    }
    jobs.append(job)
    _save(jobs)
    log_event("cron_job_added", job)
    return job


def _datetime_to_schedule(value: datetime | str) -> str:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def add_prompt_job(
    name: str,
    run_at: datetime | str,
    prompt: str,
    *,
    speaker: str = "sandro",
    enabled: bool = True,
) -> dict[str, Any]:
    jobs = _load()
    schedule = _datetime_to_schedule(run_at)
    job = {
        "id": f"cron_{uuid.uuid4().hex[:10]}",
        "kind": "prompt",
        "name": name,
        "schedule": schedule,
        "prompt": prompt,
        "speaker": speaker,
        "enabled": enabled,
        "one_shot": True,
        "created_at": now_utc().isoformat().replace("+00:00", "Z"),
        "last_run": None,
        "next_run": schedule,
        "run_count": 0,
    }
    jobs.append(job)
    _save(jobs)
    log_event("cron_prompt_job_added", {**job, "prompt": prompt[:1000]})
    return job


def list_cron_jobs() -> list[dict[str, Any]]:
    return _load()


def set_cron_enabled(job_id: str, enabled: bool) -> dict[str, Any]:
    jobs = _load()
    for job in jobs:
        if job["id"] == job_id:
            job["enabled"] = enabled
            _save(jobs)
            log_event("cron_job_enabled_changed", {"job_id": job_id, "enabled": enabled})
            return job
    raise FileNotFoundError(f"Cron job nao encontrado: {job_id}")


def run_due_jobs(*, dry_run: bool = False) -> dict[str, Any]:
    jobs = _load()
    due = []
    now = now_utc()
    for job in jobs:
        if not job.get("enabled", True):
            continue
        next_run = datetime.fromisoformat(str(job.get("next_run")).replace("Z", "+00:00"))
        if next_run <= now:
            due.append(job)
    executed = []
    for job in due:
        result = {"dry_run": dry_run}
        if not dry_run:
            if job.get("kind") == "prompt":
                completed = subprocess.run(
                    [sys.executable, "-m", "app.eve_codex", "ask", str(job.get("prompt") or ""), "--speaker", str(job.get("speaker") or "sandro")],
                    cwd=str(EVE_ROOT),
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
            else:
                completed = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", job["command"]],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
            result.update({"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
        job["last_run"] = now.isoformat().replace("+00:00", "Z")
        if job.get("kind") == "prompt" and job.get("one_shot", True):
            job["enabled"] = False
            job["next_run"] = None
        else:
            job["next_run"] = _next_run(job["schedule"], base=now)
        job["run_count"] = int(job.get("run_count") or 0) + 1
        executed.append({"job": job, "result": result})
        log_event("cron_job_executed", {"job": job, "result": result})
    _save(jobs)
    return {"executed": executed, "count": len(executed)}

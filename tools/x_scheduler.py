from __future__ import annotations

import json
import re
import sys
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

from core.paths import EVE_ROOT, LOGS_DIR, STATE_DIR, ensure_project_dirs
from security.audit_log import log_event
from tools.windows_scheduler import create_once_task


X_POST_JOBS_DIR = STATE_DIR / "x_posts"


def _safe_task_fragment(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip()).strip("_")
    return cleaned[:40] or "post"


def parse_hhmm(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*([01]?\d|2[0-3]):([0-5]\d)\s*", value)
    if not match:
        raise ValueError("Hora invalida. Usa HH:MM.")
    return int(match.group(1)), int(match.group(2))


def target_datetime_for_time(time_hhmm: str, *, now: datetime | None = None) -> tuple[datetime, str]:
    now = now or datetime.now()
    hour, minute = parse_hhmm(time_hhmm)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    note = ""
    if target <= now:
        target += timedelta(days=1)
        note = "Requested time had already passed; scheduled for the next local occurrence."
    return target, note


def build_x_post_task_command(job_path: str | Path) -> str:
    runner = EVE_ROOT / "scripts" / "run_x_post_job.py"
    return f'"{sys.executable}" "{runner}" --job "{Path(job_path)}"'


def write_x_post_job(text: str, scheduled_for: datetime, *, approved_by: str = "sandro") -> Path:
    ensure_project_dirs()
    X_POST_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    job_id = f"x_post_{scheduled_for.strftime('%Y%m%d_%H%M')}_{_safe_task_fragment(text)}"
    path = X_POST_JOBS_DIR / f"{job_id}.json"
    encoded = urllib.parse.quote(text)
    payload = {
        "id": job_id,
        "status": "scheduled",
        "platform": "x",
        "skill": "trusted/x_publish_text_learning",
        "text": text,
        "url": f"https://x.com/intent/post?text={encoded}",
        "scheduled_for": scheduled_for.isoformat(),
        "approved_by": approved_by,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "result": None,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def update_x_post_job(path: str | Path, **updates) -> dict:
    job_path = Path(path)
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    payload.update(updates)
    payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
    job_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def log_x_post_event(event: str, payload: dict) -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "x_posts.jsonl"
    row = {"timestamp": datetime.now().isoformat(timespec="seconds"), "event": event, **payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def schedule_x_post(
    text: str,
    time_hhmm: str,
    *,
    now: datetime | None = None,
    approved_by: str = "sandro",
    create_task_func=create_once_task,
) -> dict:
    text = text.strip()
    if not text:
        return {"status": "needs_confirmation", "reason": "Post text is empty."}
    target, note = target_datetime_for_time(time_hhmm, now=now)
    job_path = write_x_post_job(text, target, approved_by=approved_by)
    command = build_x_post_task_command(job_path)
    task_fragment = f"X_Post_{target.strftime('%Y%m%d_%H%M')}_{_safe_task_fragment(text)}"
    task_result = create_task_func(task_fragment, target.strftime("%H:%M"), target.strftime("%d/%m/%Y"), command)
    status = "scheduled" if int(task_result.get("returncode", 1)) == 0 else "failed"
    update_x_post_job(job_path, status=status, task_result=task_result, task_name=f"Eve_{task_fragment}", note=note)
    result = {
        "status": status,
        "task_name": f"Eve_{task_fragment}",
        "scheduled_for": target.isoformat(),
        "job_path": str(job_path),
        "text": text,
        "note": note,
        "task_result": task_result,
    }
    log_event("x_post_scheduled", result)
    log_x_post_event("scheduled", result)
    return result

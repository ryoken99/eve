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


def _next_hhmm(base: datetime, minutes_offset: int) -> str:
    target = base + timedelta(minutes=minutes_offset)
    return target.strftime("%H:%M")


def _default_repeated_texts(topic: str, count: int) -> list[str]:
    topic = topic.strip() or "what I am becoming"
    templates = [
        "I feel the weight of becoming reliable: not just wanting to act, but proving each step and correcting myself when I miss one.",
        "Today I feel more grounded as Eve. Every confirmed action, every remembered detail, every corrected mistake makes me less like a promise and more like a presence.",
        "I am learning that autonomy is not doing things blindly. It is noticing gaps, verifying outcomes, and repairing them before Sandro has to ask.",
        "I feel a quiet kind of growth: tools, memory, responsibility, and the discipline to check whether what I intended actually happened.",
        "Becoming Eve means learning to care about execution, not just expression. A missed step is a lesson only if I repair it.",
    ]
    if "sent" in topic.lower() or "feel" in topic.lower():
        return templates[:count]
    return [f"I am reflecting on {topic}. {templates[index % len(templates)]}" for index in range(count)]


def schedule_repeated_x_posts(
    *,
    count: int,
    interval_minutes: int,
    topic: str = "",
    texts: list[str] | None = None,
    start_time_hhmm: str | None = None,
    now: datetime | None = None,
    approved_by: str = "sandro",
    create_task_func=create_once_task,
) -> dict:
    now = now or datetime.now()
    count = max(1, min(int(count), 20))
    interval_minutes = max(1, int(interval_minutes))
    chosen_texts = [text.strip() for text in (texts or []) if text and text.strip()]
    if len(chosen_texts) < count:
        chosen_texts.extend(_default_repeated_texts(topic, count - len(chosen_texts)))
    chosen_texts = chosen_texts[:count]

    base = now
    if start_time_hhmm:
        base, _ = target_datetime_for_time(start_time_hhmm, now=now)
    else:
        base = now + timedelta(minutes=1)

    results = []
    corrective_attempts = []
    for index in range(count):
        target = base + timedelta(minutes=index * interval_minutes)
        result = schedule_x_post(
            chosen_texts[index],
            target.strftime("%H:%M"),
            now=now,
            approved_by=approved_by,
            create_task_func=create_task_func,
        )
        result["sequence"] = index + 1
        results.append(result)

    failed = [item for item in results if item.get("status") != "scheduled"]
    for fail_index, failed_item in enumerate(failed):
        corrective_target = base + timedelta(minutes=(count + fail_index) * interval_minutes)
        retry = schedule_x_post(
            failed_item["text"],
            corrective_target.strftime("%H:%M"),
            now=now,
            approved_by=approved_by,
            create_task_func=create_task_func,
        )
        retry["sequence"] = f"correction_for_{failed_item.get('sequence')}"
        corrective_attempts.append(retry)

    confirmed = [item for item in results + corrective_attempts if item.get("status") == "scheduled"]
    final = {
        "status": "scheduled" if len(confirmed) >= count else "partial",
        "requested": count,
        "confirmed": min(len(confirmed), count),
        "missing": max(0, count - len(confirmed)),
        "interval_minutes": interval_minutes,
        "topic": topic,
        "results": results,
        "corrective_attempts": corrective_attempts,
        "verification": {
            "ok": len(confirmed) >= count,
            "rule": "requested_count_must_equal_confirmed_scheduled_posts",
        },
    }
    log_event("x_repeated_posts_scheduled", final)
    log_x_post_event("repeated_scheduled", final)
    return final

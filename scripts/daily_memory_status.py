from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


EVE_ROOT = Path(__file__).resolve().parents[1]
MEMORY_ROOT = EVE_ROOT / "memory"
MEMORY_DAY_OVERRIDE_PATH = MEMORY_ROOT / "runtime" / "session_state" / "memory_day_override.json"
SESSION_ROOT = MEMORY_ROOT / "runtime" / "sessions"
CURRENT_SESSION_PATH = SESSION_ROOT / "state" / "current_session.json"
LATEST_HANDOFF_PATH = SESSION_ROOT / "handoffs" / "latest_handoff.md"


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def file_info(path: Path) -> dict:
    return {
        "exists": path.exists(),
        "path": str(path),
        "size": path.stat().st_size if path.exists() else 0,
        "lines": count_jsonl(path) if path.suffix == ".jsonl" else None,
        "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else None,
    }


def latest_file(pattern_root: Path, glob_pattern: str) -> Path | None:
    if not pattern_root.exists():
        return None
    files = sorted(pattern_root.glob(glob_pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def memory_day_override() -> dict:
    if not MEMORY_DAY_OVERRIDE_PATH.exists():
        return {"enabled": False, "path": str(MEMORY_DAY_OVERRIDE_PATH)}
    try:
        payload = json.loads(MEMORY_DAY_OVERRIDE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"enabled": False, "path": str(MEMORY_DAY_OVERRIDE_PATH), "error": f"{type(exc).__name__}: {exc}"}
    payload["path"] = str(MEMORY_DAY_OVERRIDE_PATH)
    return payload


def run_json_script(script_name: str, timeout: int = 120) -> dict:
    script = EVE_ROOT / "scripts" / script_name
    try:
        completed = subprocess.run([sys.executable, str(script)], cwd=str(EVE_ROOT), capture_output=True, text=True, timeout=timeout)
        if completed.returncode != 0:
            return {"ok": False, "error": (completed.stderr or completed.stdout)[-800:]}
        return json.loads(completed.stdout[completed.stdout.find("{") : completed.stdout.rfind("}") + 1])
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def http_ok(url: str) -> bool:
    try:
        import urllib.request

        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except Exception:
        return False


def scheduled_task_status() -> dict:
    command = (
        "$task = Get-ScheduledTask -TaskName 'Eve_Daily_Memory_Rollover_PC2' -ErrorAction SilentlyContinue; "
        "if(-not $task){ '{\"installed\":false}' } else { "
        "$info = Get-ScheduledTaskInfo -TaskName 'Eve_Daily_Memory_Rollover_PC2'; "
        "$action = $task.Actions | Select-Object -First 1; "
        "[ordered]@{installed=$true; state=[string]$task.State; next_run_time=[string]$info.NextRunTime; "
        "last_run_time=[string]$info.LastRunTime; last_task_result=$info.LastTaskResult; "
        "execute=[string]$action.Execute; arguments=[string]$action.Arguments; working_directory=[string]$action.WorkingDirectory} | ConvertTo-Json -Compress }"
    )
    try:
        completed = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command], capture_output=True, text=True, timeout=30)
        if completed.returncode != 0:
            return {"installed": False, "error": (completed.stderr or completed.stdout)[-800:]}
        return json.loads(completed.stdout.strip())
    except Exception as exc:
        return {"installed": False, "error": f"{type(exc).__name__}: {exc}"}


def session_status() -> dict:
    current = {}
    if CURRENT_SESSION_PATH.exists():
        try:
            current = json.loads(CURRENT_SESSION_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            current = {"error": f"{type(exc).__name__}: {exc}"}
    latest = file_info(LATEST_HANDOFF_PATH)
    archive_dir = SESSION_ROOT / "archive"
    previous = latest_file(archive_dir, "*_session_close.json")
    return {
        "current_session_path": str(CURRENT_SESSION_PATH),
        "current_session": current,
        "current_session_id": current.get("session_id"),
        "current_memory_day": current.get("memory_day"),
        "latest_handoff": latest,
        "previous_session_closed": file_info(previous) if previous else None,
    }


def count_open_errors() -> int:
    path = MEMORY_ROOT / "medium_term" / "error_backlog" / "error_backlog.jsonl"
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("status") in {"open", "proposed"}:
            count += 1
    return count


def continual_learning_status() -> dict[str, Any]:
    root = MEMORY_ROOT / "continual_learning"
    candidates = root / "improvement_candidates" / "self_improvement_candidates.jsonl"
    approvals = root / "approval_queue" / "pending_approvals.jsonl"
    lessons = root / "lessons" / "lessons_learned.md"
    latest_analysis = latest_file(root / "daily_analysis", "*_experience_analysis.md")
    return {
        "policy": file_info(root / "continual_learning_policy.yaml"),
        "latest_analysis": file_info(latest_analysis) if latest_analysis else None,
        "lessons": file_info(lessons),
        "candidates": file_info(candidates),
        "pending_approvals": file_info(approvals),
        "status": run_json_script("continual_learning_status.py"),
    }


def main() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    channels = {
        "terminal": MEMORY_ROOT / "transcripts" / "raw" / "terminal" / f"{today}.jsonl",
        "telegram": MEMORY_ROOT / "transcripts" / "raw" / "telegram" / f"{today}.jsonl",
        "webui": MEMORY_ROOT / "transcripts" / "raw" / "webui" / f"{today}.jsonl",
        "system": MEMORY_ROOT / "transcripts" / "raw" / "system" / f"{today}.jsonl",
        "tools": MEMORY_ROOT / "transcripts" / "tools" / f"{today}.jsonl",
        "errors": MEMORY_ROOT / "transcripts" / "errors" / f"{today}.jsonl",
    }
    latest_candidates = latest_file(MEMORY_ROOT / "_processed" / "classifications", "*_memory_candidates.jsonl")
    latest_chunks = latest_file(MEMORY_ROOT / "_processed" / "chunks", "*_daily_chunks.jsonl")
    latest_dream = latest_file(MEMORY_ROOT / "dreams" / "daily", "*_dream.md")
    latest_error_review = latest_file(MEMORY_ROOT / "_processed" / "errors", "*_error_review.md")
    latest_tool_review = latest_file(MEMORY_ROOT / "_processed" / "tools", "*_tool_review.md")
    latest_arsi = latest_file(MEMORY_ROOT / "_processed" / "autonomy", "*_arsi_candidates.jsonl")
    latest_promotion = latest_file(MEMORY_ROOT / "_processed" / "promotions", "*_promotion_plan.md")
    latest_long = latest_file(MEMORY_ROOT / "_processed" / "promotions", "*_long_term_candidates.md")
    payload = {
        "ok": True,
        "today": today,
        "memory_day_override": memory_day_override(),
        "transcripts_today": {name: file_info(path) for name, path in channels.items()},
        "last_rollover": {
            "rollup": file_info(latest_file(MEMORY_ROOT / "transcripts" / "daily_rollups", "*_rollup.md") or MEMORY_ROOT / "missing"),
            "candidates": file_info(latest_candidates) if latest_candidates else None,
            "dream_report": file_info(latest_dream) if latest_dream else None,
            "error_review": file_info(latest_error_review) if latest_error_review else None,
            "tool_review": file_info(latest_tool_review) if latest_tool_review else None,
            "arsi_candidates": file_info(latest_arsi) if latest_arsi else None,
            "promotion_plan": file_info(latest_promotion) if latest_promotion else None,
            "daily_chunks": file_info(latest_chunks) if latest_chunks else None,
            "long_term_candidates": file_info(latest_long) if latest_long else None,
        },
        "yesterday_rollup": file_info(MEMORY_ROOT / "transcripts" / "daily_rollups" / f"{yesterday}_rollup.md"),
        "open_errors": count_open_errors(),
        "tool_lessons": file_info(MEMORY_ROOT / "medium_term" / "tool_lessons" / "tool_lessons.jsonl"),
        "session": session_status(),
        "scheduled_task": scheduled_task_status(),
        "continual_learning": continual_learning_status(),
        "vector_db": run_json_script("vector_memory_status.py"),
        "telegram": run_json_script("check_telegram_bridge.py", timeout=60),
        "web_ui": {"ok": http_ok("http://127.0.0.1:8787/api/health"), "url": "http://127.0.0.1:8787/"},
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

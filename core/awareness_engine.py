from __future__ import annotations

import getpass
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVE_ROOT = Path(__file__).resolve().parents[1]
MEMORY_ROOT = EVE_ROOT / "memory"
AWARENESS_ROOT = MEMORY_ROOT / "runtime" / "awareness"
REPORTS_DIR = AWARENESS_ROOT / "reports"
STATE_DIR = AWARENESS_ROOT / "state"
SNAPSHOT_DIR = AWARENESS_ROOT / "snapshots"
MEMORY_REPORTS_DIR = MEMORY_ROOT / "_reports"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_awareness_dirs() -> None:
    for path in (
        STATE_DIR,
        SNAPSHOT_DIR,
        REPORTS_DIR,
        AWARENESS_ROOT / "file_changes",
        AWARENESS_ROOT / "code_changes",
        AWARENESS_ROOT / "health",
        AWARENESS_ROOT / "heartbeats",
        AWARENESS_ROOT / "startup_shutdown",
        AWARENESS_ROOT / "tasks",
        MEMORY_REPORTS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def run_command(args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=EVE_ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}


def read_json(path: Path, default: Any = None) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return {"_error": str(exc), "_path": str(path)}


def file_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    stat = path.stat()
    return {
        "exists": True,
        "path": str(path),
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def http_check(url: str, timeout: int = 3) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(512).decode("utf-8", errors="replace")
            return {"ok": 200 <= response.status < 400, "status": response.status, "url": url, "sample": body[:120]}
    except Exception as exc:
        return {"ok": False, "status": None, "url": url, "error": str(exc)}


def get_pc_identity() -> dict[str, Any]:
    local_time = datetime.now().astimezone()
    return {
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "timezone": local_time.tzname(),
        "local_time": local_time.isoformat(timespec="seconds"),
        "eve_root": str(EVE_ROOT),
        "expected_root": "E:\\eve",
        "root_is_expected": str(EVE_ROOT).lower() == "e:\\eve",
        "pc_role": "PC2 primary_runtime_home",
        "pc1_role": "builder_dev_workshop",
    }


def get_runtime_paths() -> dict[str, Any]:
    paths = {
        "eve_root": EVE_ROOT,
        "memory": MEMORY_ROOT,
        "transcripts": MEMORY_ROOT / "transcripts",
        "vector": MEMORY_ROOT / "vector" / "chroma",
        "current_session": MEMORY_ROOT / "runtime" / "sessions" / "state" / "current_session.json",
        "latest_handoff": MEMORY_ROOT / "runtime" / "sessions" / "handoffs" / "latest_handoff.md",
        "rollover_script": EVE_ROOT / "scripts" / "daily_memory_rollover.py",
    }
    return {name: file_info(path) for name, path in paths.items()}


def get_python_environment() -> dict[str, Any]:
    pip = EVE_ROOT / ".venv" / "Scripts" / "pip.exe"
    python = EVE_ROOT / ".venv" / "Scripts" / "python.exe"
    packages = {}
    if pip.exists():
        for package in ("chromadb", "requests", "playwright", "uiautomation", "pyautogui", "pytesseract"):
            result = run_command([str(pip), "show", package], timeout=10)
            packages[package] = {"installed": result["ok"]}
    return {
        "python_path": str(python),
        "python_exists": python.exists(),
        "venv_exists": (EVE_ROOT / ".venv").exists(),
        "packages": packages,
    }


def get_process_status() -> dict[str, Any]:
    ps = run_command(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'eve_web|telegram_bridge|ollama|python' } | Select-Object ProcessId,CommandLine | ConvertTo-Json -Depth 3",
        ],
        timeout=20,
    )
    return {"ok": ps["ok"], "processes_json": ps["stdout"][:12000], "error": ps["stderr"]}


def _script_json(script: str, timeout: int = 60) -> dict[str, Any]:
    python = EVE_ROOT / ".venv" / "Scripts" / "python.exe"
    path = EVE_ROOT / "scripts" / script
    if not python.exists() or not path.exists():
        return {"ok": False, "error": f"missing {python if not python.exists() else path}"}
    result = run_command([str(python), str(path)], timeout=timeout)
    if not result["ok"]:
        return {"ok": False, "error": result["stderr"] or result["stdout"]}
    try:
        return json.loads(result["stdout"])
    except Exception:
        return {"ok": True, "raw": result["stdout"]}


def get_service_status() -> dict[str, Any]:
    telegram = _script_json("check_telegram_bridge.py", timeout=30)
    ollama = http_check("http://127.0.0.1:11434/api/tags", timeout=3)
    return {
        "webui": http_check("http://127.0.0.1:8787/api/health", timeout=3),
        "telegram": telegram,
        "ollama": ollama,
        "rollover_task": get_scheduled_tasks_status().get("daily_rollover"),
    }


def get_git_status() -> dict[str, Any]:
    branch = run_command(["git", "branch", "--show-current"])
    commit = run_command(["git", "rev-parse", "--short", "HEAD"])
    status = run_command(["git", "status", "--short"], timeout=30)
    files = [line for line in status["stdout"].splitlines() if line.strip()]
    return {
        "branch": branch["stdout"],
        "commit": commit["stdout"],
        "dirty": bool(files),
        "changed_count": len(files),
        "changed_files": files[:80],
        "truncated": len(files) > 80,
    }


def get_vector_status() -> dict[str, Any]:
    return _script_json("vector_memory_status.py", timeout=60)


def get_memory_status() -> dict[str, Any]:
    status = _script_json("daily_memory_status.py", timeout=90)
    if not isinstance(status, dict):
        return {"ok": False, "error": "unexpected memory status"}
    return status


def get_session_status() -> dict[str, Any]:
    session_path = MEMORY_ROOT / "runtime" / "sessions" / "state" / "current_session.json"
    handoff_path = MEMORY_ROOT / "runtime" / "sessions" / "handoffs" / "latest_handoff.md"
    session = read_json(session_path, {})
    return {
        "current_session": session,
        "current_session_file": file_info(session_path),
        "latest_handoff": file_info(handoff_path),
    }


def get_rollover_status() -> dict[str, Any]:
    memory = get_memory_status()
    return {
        "last_rollover": memory.get("last_rollover", {}),
        "scheduled_task": memory.get("scheduled_task", {}),
        "override": memory.get("memory_day_override"),
    }


def get_scheduled_tasks_status() -> dict[str, Any]:
    cmd = (
        "$t=Get-ScheduledTask -TaskName 'Eve_Daily_Memory_Rollover_PC2' -ErrorAction SilentlyContinue; "
        "if($t){$i=Get-ScheduledTaskInfo -TaskName 'Eve_Daily_Memory_Rollover_PC2'; "
        "[PSCustomObject]@{installed=$true;state=$t.State.ToString();next_run_time=$i.NextRunTime.ToString();last_run_time=$i.LastRunTime.ToString();last_task_result=$i.LastTaskResult} | ConvertTo-Json} "
        "else {[PSCustomObject]@{installed=$false} | ConvertTo-Json}"
    )
    result = run_command(["powershell.exe", "-NoProfile", "-Command", cmd], timeout=20)
    try:
        daily = json.loads(result["stdout"]) if result["stdout"] else {"installed": False}
    except Exception:
        daily = {"installed": False, "error": result["stderr"] or result["stdout"]}
    return {"daily_rollover": daily}


def get_transcript_status() -> dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")
    channels = {
        "terminal": MEMORY_ROOT / "transcripts" / "raw" / "terminal" / f"{today}.jsonl",
        "telegram": MEMORY_ROOT / "transcripts" / "raw" / "telegram" / f"{today}.jsonl",
        "webui": MEMORY_ROOT / "transcripts" / "raw" / "webui" / f"{today}.jsonl",
        "system": MEMORY_ROOT / "transcripts" / "raw" / "system" / f"{today}.jsonl",
        "tools": MEMORY_ROOT / "transcripts" / "tools" / f"{today}.jsonl",
        "errors": MEMORY_ROOT / "transcripts" / "errors" / f"{today}.jsonl",
    }
    rows = {}
    for name, path in channels.items():
        info = file_info(path)
        if path.exists():
            try:
                info["lines"] = sum(1 for _ in path.open("r", encoding="utf-8", errors="replace"))
            except Exception:
                info["lines"] = None
        rows[name] = info
    return rows


def get_last_errors_status() -> dict[str, Any]:
    errors_dir = MEMORY_ROOT / "transcripts" / "errors"
    reviews_dir = MEMORY_ROOT / "_processed" / "errors"
    latest_error_file = max(errors_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, default=None) if errors_dir.exists() else None
    latest_review = max(reviews_dir.glob("*_error_review.md"), key=lambda p: p.stat().st_mtime, default=None) if reviews_dir.exists() else None
    return {
        "latest_error_transcript": file_info(latest_error_file) if latest_error_file else {"exists": False},
        "latest_error_review": file_info(latest_review) if latest_review else {"exists": False},
    }


def _active_window_title() -> str:
    result = run_command(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "Add-Type 'using System; using System.Runtime.InteropServices; public class W { [DllImport(\"user32.dll\")] public static extern IntPtr GetForegroundWindow(); [DllImport(\"user32.dll\")] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count); }'; $b=New-Object System.Text.StringBuilder 512; [void][W]::GetWindowText([W]::GetForegroundWindow(), $b, $b.Capacity); $b.ToString()",
        ],
        timeout=10,
    )
    return result.get("stdout") or "unknown"


def collect_awareness() -> dict[str, Any]:
    """Backward-compatible lightweight awareness snapshot used by older Eve code."""
    pc = get_pc_identity()
    session = read_json(MEMORY_ROOT / "runtime" / "sessions" / "state" / "current_session.json", {}) or {}
    return {
        "timestamp": now_iso(),
        "timezone": "Europe/Lisbon",
        "eve": {
            "name": "Eve",
            "mode": "unrestricted_mode",
            "root": str(EVE_ROOT),
            "pc_role": "PC2 primary_runtime_home",
            "active_project": "Eve PC2 runtime",
            "active_task": "operational self-awareness",
            "session_id": session.get("session_id"),
            "memory_day": session.get("memory_day"),
        },
        "desktop": {
            "active_window": _active_window_title(),
        },
        "system": {
            "os": "Windows" if platform.system().lower().startswith("win") else platform.system(),
            "hostname": pc.get("hostname"),
            "username": pc.get("username"),
        },
        "services": {
            "webui": http_check("http://127.0.0.1:8787/api/health", timeout=2),
            "ollama": http_check("http://127.0.0.1:11434/api/tags", timeout=2),
        },
    }


def describe_awareness() -> str:
    awareness = collect_awareness()
    return "\n".join(
        [
            "Eve awareness:",
            f"- Tempo: {awareness['timestamp']} ({awareness['timezone']})",
            f"- Root: {awareness['eve']['root']}",
            f"- Role: {awareness['eve']['pc_role']}",
            f"- Sessao: {awareness['eve'].get('session_id')} / {awareness['eve'].get('memory_day')}",
            f"- Janela ativa: {awareness['desktop'].get('active_window')}",
            f"- Web UI: {'ok' if awareness['services']['webui'].get('ok') else 'fail'}",
            f"- Ollama: {'ok' if awareness['services']['ollama'].get('ok') else 'fail'}",
        ]
    )


def build_self_state() -> dict[str, Any]:
    memory_status = get_memory_status()
    vector_status = memory_status.get("vector_db") or get_vector_status()
    services = {
        "webui": memory_status.get("web_ui") or http_check("http://127.0.0.1:8787/api/health"),
        "telegram": memory_status.get("telegram") or _script_json("check_telegram_bridge.py"),
        "ollama": (vector_status or {}).get("ollama_status") or http_check("http://127.0.0.1:11434/api/tags"),
        "vector_db": vector_status,
    }
    git = get_git_status()
    session = memory_status.get("session") or get_session_status()
    summary_status = "ok"
    if not services["webui"].get("ok") or not services["telegram"].get("running") or not services["ollama"].get("ok"):
        summary_status = "warning"
    return {
        "timestamp": now_iso(),
        "pc_identity": get_pc_identity(),
        "runtime_paths": get_runtime_paths(),
        "python_environment": get_python_environment(),
        "services": services,
        "git": git,
        "memory": memory_status,
        "vector": vector_status,
        "session": session,
        "rollover": {
            "last_rollover": memory_status.get("last_rollover"),
            "scheduled_task": memory_status.get("scheduled_task"),
            "override": memory_status.get("memory_day_override"),
        },
        "scheduled_tasks": get_scheduled_tasks_status(),
        "transcripts": memory_status.get("transcripts_today") or get_transcript_status(),
        "errors": {"open_errors": memory_status.get("open_errors"), **get_last_errors_status()},
        "health_summary": {
            "overall_status": summary_status,
            "webui_ok": bool(services["webui"].get("ok")),
            "telegram_running": bool(services["telegram"].get("running")),
            "ollama_ok": bool(services["ollama"].get("ok")),
            "git_dirty": bool(git.get("dirty")),
        },
    }


def write_self_state(state: dict[str, Any] | None = None) -> Path:
    ensure_awareness_dirs()
    state = state or build_self_state()
    path = STATE_DIR / "current_self_state.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_awareness_snapshot(state: dict[str, Any] | None = None) -> Path:
    ensure_awareness_dirs()
    state = state or build_self_state()
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = SNAPSHOT_DIR / f"{stamp}_awareness_snapshot.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def compact_self_state_text(state: dict[str, Any] | None = None, max_chars: int = 1000) -> str:
    state = state or read_json(STATE_DIR / "current_self_state.json", {}) or {}
    pc = state.get("pc_identity", {})
    session = (state.get("session") or {}).get("current_session") or {}
    services = state.get("services", {})
    rollover = state.get("rollover", {})
    lines = [
        f"Eve runtime: {pc.get('pc_role', 'PC2 primary_runtime_home')} em {pc.get('eve_root', 'E:/eve')}.",
        f"Sessao: {session.get('session_id', 'unknown')} / memory_day {session.get('memory_day', 'unknown')}.",
        f"Servicos: Web UI={'ok' if services.get('webui', {}).get('ok') else 'fail'}, Telegram={'ok' if services.get('telegram', {}).get('running') else 'fail'}, Ollama={'ok' if services.get('ollama', {}).get('ok') else 'fail'}.",
        f"Ultimo rollover: {((rollover.get('last_rollover') or {}).get('rollup') or {}).get('path', 'unknown')}.",
        f"Handoff: {(((state.get('session') or {}).get('latest_handoff') or {}).get('path', 'unknown'))}.",
        f"Git: {state.get('git', {}).get('branch', 'unknown')} {state.get('git', {}).get('commit', '')}, dirty={state.get('git', {}).get('dirty')}.",
    ]
    text = "\n".join(lines)
    return text[:max_chars]


def write_awareness_report(state: dict[str, Any] | None = None) -> Path:
    ensure_awareness_dirs()
    state = state or build_self_state()
    today = datetime.now().strftime("%Y-%m-%d")
    path = REPORTS_DIR / f"{today}_awareness_report.md"
    report = [
        "# Eve Awareness Report",
        "",
        f"Generated: {state.get('timestamp')}",
        "",
        "## Identity",
        f"- Root: {state.get('pc_identity', {}).get('eve_root')}",
        f"- Role: {state.get('pc_identity', {}).get('pc_role')}",
        f"- Host: {state.get('pc_identity', {}).get('hostname')}",
        "",
        "## Services",
        f"- Web UI: {state.get('health_summary', {}).get('webui_ok')}",
        f"- Telegram: {state.get('health_summary', {}).get('telegram_running')}",
        f"- Ollama: {state.get('health_summary', {}).get('ollama_ok')}",
        "",
        "## Session",
        f"- Current: {((state.get('session') or {}).get('current_session') or {}).get('session_id')}",
        f"- Memory day: {((state.get('session') or {}).get('current_session') or {}).get('memory_day')}",
        f"- Latest handoff: {(((state.get('session') or {}).get('latest_handoff') or {}).get('path'))}",
        "",
        "## Rollover",
        f"- Scheduled task: {((state.get('rollover') or {}).get('scheduled_task') or {}).get('state')}",
        f"- Last task result: {((state.get('rollover') or {}).get('scheduled_task') or {}).get('last_task_result')}",
        "",
        "## Git",
        f"- Branch: {state.get('git', {}).get('branch')}",
        f"- Commit: {state.get('git', {}).get('commit')}",
        f"- Dirty: {state.get('git', {}).get('dirty')} ({state.get('git', {}).get('changed_count')} files)",
    ]
    path.write_text("\n".join(report) + "\n", encoding="utf-8")
    return path


def write_initial_audit_report() -> Path:
    state = build_self_state()
    path = MEMORY_REPORTS_DIR / "pc2_awareness_initial_audit.md"
    lines = [
        "# PC2 Awareness Initial Audit",
        "",
        f"Generated: {state['timestamp']}",
        f"Root detected: {state['pc_identity']['eve_root']}",
        f"Web UI status: {state['health_summary']['webui_ok']}",
        f"Telegram status: {state['health_summary']['telegram_running']}",
        f"Ollama status: {state['health_summary']['ollama_ok']}",
        f"Vector status: {bool((state.get('vector') or {}).get('chroma_exists'))}",
        f"Current session exists: {bool(((state.get('session') or {}).get('current_session') or {}).get('session_id'))}",
        f"Latest handoff exists: {((state.get('session') or {}).get('latest_handoff') or {}).get('exists')}",
        f"Rollover task: {((state.get('rollover') or {}).get('scheduled_task') or {}).get('state')}",
        "",
        "Risks detected:",
        f"- Git dirty: {state['git']['dirty']} with {state['git']['changed_count']} changed files.",
        f"- Memory day override: {bool((state.get('rollover') or {}).get('override'))}.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path

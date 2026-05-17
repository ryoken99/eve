from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


EVE_ROOT = Path(__file__).resolve().parents[1]
HEARTBEAT_DIR = EVE_ROOT / "memory" / "runtime" / "awareness" / "heartbeats"
STARTUP_DIR = EVE_ROOT / "memory" / "runtime" / "awareness" / "startup_shutdown"
CURRENT_SESSION_PATH = EVE_ROOT / "memory" / "runtime" / "sessions" / "state" / "current_session.json"
HEARTBEAT_PATH = HEARTBEAT_DIR / "heartbeat.json"
HEARTBEAT_HISTORY_PATH = HEARTBEAT_DIR / "heartbeat_history.jsonl"
STARTUP_LOG_PATH = STARTUP_DIR / "startup_shutdown_log.jsonl"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_dirs() -> None:
    HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
    STARTUP_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return default


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def current_session_summary() -> dict[str, Any]:
    session = _read_json(CURRENT_SESSION_PATH, {}) or {}
    return {
        "session_id": session.get("session_id"),
        "memory_day": session.get("memory_day"),
    }


def write_heartbeat(source: str = "runtime") -> dict[str, Any]:
    ensure_dirs()
    session = current_session_summary()
    heartbeat = {
        "timestamp": now_iso(),
        "source": source,
        "process_id": os.getpid(),
        "session_id": session.get("session_id"),
        "memory_day": session.get("memory_day"),
        "pc_role": "PC2 primary_runtime_home",
    }
    HEARTBEAT_PATH.write_text(json.dumps(heartbeat, ensure_ascii=False, indent=2), encoding="utf-8")
    _append_jsonl(HEARTBEAT_HISTORY_PATH, heartbeat)
    return heartbeat


def read_last_heartbeat() -> dict[str, Any] | None:
    return _read_json(HEARTBEAT_PATH, None)


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def estimate_uptime() -> dict[str, Any]:
    last = read_last_heartbeat()
    if not last:
        return {"known": False, "seconds_since_last_heartbeat": None}
    ts = _parse_time(last.get("timestamp"))
    if not ts:
        return {"known": False, "seconds_since_last_heartbeat": None}
    return {"known": True, "seconds_since_last_heartbeat": max(0, int((datetime.now().astimezone() - ts).total_seconds()))}


def estimate_offline_time() -> dict[str, Any]:
    last = read_last_heartbeat()
    if not last:
        return {"known": False, "offline_seconds": None}
    ts = _parse_time(last.get("timestamp"))
    if not ts:
        return {"known": False, "offline_seconds": None}
    return {"known": True, "offline_seconds": max(0, int((datetime.now().astimezone() - ts).total_seconds()))}


def detect_unclean_shutdown(threshold_seconds: int = 600) -> bool:
    offline = estimate_offline_time()
    return bool(offline.get("known") and (offline.get("offline_seconds") or 0) > threshold_seconds)


def write_startup_event() -> dict[str, Any]:
    ensure_dirs()
    last = read_last_heartbeat()
    event = {
        "event": "startup",
        "started_at": now_iso(),
        "last_heartbeat_before_start": last,
        "estimated_offline_time": estimate_offline_time(),
        "unclean_shutdown": detect_unclean_shutdown(),
    }
    _append_jsonl(STARTUP_LOG_PATH, event)
    return event


def write_shutdown_event(reason: str = "manual") -> dict[str, Any]:
    ensure_dirs()
    event = {
        "event": "shutdown",
        "stopped_at": now_iso(),
        "reason": reason,
        "clean_shutdown": True,
    }
    _append_jsonl(STARTUP_LOG_PATH, event)
    return event

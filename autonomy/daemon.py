from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from autonomy.proactive_decider import propose_low_risk_actions
from autonomy.autonomy_director import run_autonomy_cycle
from core.paths import LOGS_DIR, STATE_DIR, ensure_project_dirs
from memory.semantic_vector.vector_store import rebuild_memory_index
from research.technology_watcher import run_technology_watch


STOP_FILE = STATE_DIR / "daemon.stop"
HEARTBEAT = STATE_DIR / "daemon_heartbeat.json"


def daemon_tick() -> dict:
    ensure_project_dirs()
    proposals = propose_low_risk_actions()
    autonomy = run_autonomy_cycle(triggers=["daemon_tick"], max_new_missions=1, call_llm=False, cycle_name="daemon_tick")
    vector = rebuild_memory_index()
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "proposals": proposals,
        "autonomy": {
            "created_missions": autonomy["created_missions"],
            "llm_called": autonomy["llm_called"],
        },
        "vector_index": str(vector),
    }
    HEARTBEAT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def run_daemon(interval_seconds: int = 900) -> None:
    ensure_project_dirs()
    while not STOP_FILE.exists():
        daemon_tick()
        time.sleep(max(10, interval_seconds))


def request_daemon_stop() -> Path:
    ensure_project_dirs()
    STOP_FILE.write_text("stop", encoding="utf-8")
    return STOP_FILE

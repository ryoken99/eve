from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from autonomy.proactive_decider import propose_low_risk_actions
from autonomy.autonomy_director import run_autonomy_cycle
from autonomy.autonomous_executor import execute_autonomous_backlog
from autonomy.cron_manager import run_due_jobs
from autonomy.trigger_engine import create_missions_from_triggers, discover_triggers
from autonomy.capability_roadmap import append_capability_review_history, capability_audit, ensure_capability_review_schedule, write_capability_audit
from core.mission_control import list_missions
from core.paths import LOGS_DIR, STATE_DIR, ensure_project_dirs
from memory.vector_provider import rebuild_vector_memory
from memory.daily_transcripts import ensure_daily_transcript_files
from research.technology_watcher import run_technology_watch


STOP_FILE = STATE_DIR / "daemon.stop"
HEARTBEAT = STATE_DIR / "daemon_heartbeat.json"


def daemon_tick() -> dict:
    ensure_project_dirs()
    transcripts = ensure_daily_transcript_files()
    cron = run_due_jobs(dry_run=False)
    triggers = discover_triggers()
    proposed_backlog = list_missions(status="proposed", limit=10)
    trigger_missions = {"created": []}
    if not proposed_backlog:
        trigger_missions = create_missions_from_triggers(max_new=1)
    proposals = propose_low_risk_actions()
    trigger_kinds = [str(item.get("kind") or "trigger") for item in triggers[:5]]
    autonomy = run_autonomy_cycle(
        triggers=["daemon_tick", *trigger_kinds],
        max_new_missions=1,
        call_llm="auto",
        cycle_name="daemon_tick",
    )
    autonomous_execution = execute_autonomous_backlog(max_missions=1, notify_chat=True)
    vector = rebuild_vector_memory()
    capability_path = write_capability_audit()
    capability_history = append_capability_review_history()
    capability_schedule = ensure_capability_review_schedule()
    capability = capability_audit()
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "transcripts": transcripts,
        "cron": cron,
        "triggers": {"discovered": trigger_kinds, "created_missions": trigger_missions.get("created", [])},
        "proposals": proposals,
        "autonomy": {
            "created_missions": autonomy["created_missions"],
            "executed_missions": autonomous_execution["executed"],
            "token_decision": autonomy["token_decision"],
            "llm_called": autonomy["llm_called"],
        },
        "vector_index": vector,
        "capability_roadmap": {
            "summary": capability["summary"],
            "weakest": capability["weakest"],
            "path": str(capability_path),
            "history": str(capability_history),
            "schedule": capability_schedule,
        },
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

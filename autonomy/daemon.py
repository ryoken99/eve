from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from autonomy.proactive_decider import decide_proactive_actions
from autonomy.autonomy_director import run_autonomy_cycle
from autonomy.autonomous_executor import execute_autonomous_backlog
from autonomy.cron_manager import run_due_jobs
from autonomy.trigger_engine import create_missions_from_triggers, discover_triggers
from autonomy.capability_goal_harness import run_capability_goal_harness
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
    proposals = decide_proactive_actions()
    trigger_kinds = [str(item.get("kind") or "trigger") for item in triggers[:5]]
    autonomy = run_autonomy_cycle(
        triggers=["daemon_tick", *trigger_kinds],
        max_new_missions=1,
        call_llm="auto",
        cycle_name="daemon_tick",
    )
    autonomous_execution = execute_autonomous_backlog(max_missions=1, notify_chat=True)
    vector = rebuild_vector_memory()
    capability_goal = run_capability_goal_harness(ensure_schedules=True, write_report=True)
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "transcripts": transcripts,
        "cron": cron,
        "triggers": {"discovered": trigger_kinds, "created_missions": trigger_missions.get("created", [])},
        "proposals": proposals["actions"],
        "proactive_decisions": {"count": proposals["count"], "log_path": proposals["log_path"]},
        "autonomy": {
            "created_missions": autonomy["created_missions"],
            "executed_missions": autonomous_execution["executed"],
            "token_decision": autonomy["token_decision"],
            "llm_called": autonomy["llm_called"],
        },
        "vector_index": vector,
        "capability_goal_harness": {
            "summary": capability_goal["summary"],
            "all_meet_target": capability_goal["all_meet_target"],
            "points_below_target": [
                {"id": item["id"], "title": item["title"], "score_10": item["score_10"]}
                for item in capability_goal["points_below_target"]
            ],
            "report_path": capability_goal.get("report_path"),
            "log_path": capability_goal.get("log_path"),
            "setup": capability_goal["setup"],
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

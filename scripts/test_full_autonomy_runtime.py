from __future__ import annotations

from runtime_validation_lib import check, finalize

from autonomy.daemon import HEARTBEAT, daemon_tick
from autonomy.trigger_engine import discover_triggers
from core.mission_control import list_missions
from core.paths import STATE_DIR


def main() -> dict:
    first = daemon_tick()
    second = daemon_tick()
    third = daemon_tick()
    triggers = discover_triggers()
    missions = list_missions(limit=20)
    checks = [
        check("daemon tick returns heartbeat payload", bool(first.get("timestamp")), first, critical=True),
        check("daemon tick can run three times", all(row.get("timestamp") for row in (first, second, third)), {"runs": [first.get("timestamp"), second.get("timestamp"), third.get("timestamp")]}, critical=True),
        check("daemon heartbeat file exists", HEARTBEAT.exists(), str(HEARTBEAT), critical=True),
        check("cron result present", "cron" in first, first.get("cron"), critical=True),
        check("trigger discovery works", isinstance(triggers, list), triggers, critical=True),
        check("missions list can be read", isinstance(missions, list), {"count": len(missions)}, critical=True),
        check("vector rebuild ran during daemon", bool(first.get("vector_index", {}).get("index")), first.get("vector_index"), critical=True),
        check("capability goal harness ran during daemon", bool(first.get("capability_goal_harness", {}).get("report_path")), first.get("capability_goal_harness"), critical=True),
        check("proactive decisions log is present", bool(first.get("proactive_decisions", {}).get("log_path")), first.get("proactive_decisions")),
    ]
    return finalize("point_17_autonomy_runtime", "Point 17 Full Autonomy Runtime", "point_17_autonomy_runtime.md", checks)


if __name__ == "__main__":
    main()

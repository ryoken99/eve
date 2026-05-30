from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_MAP = ROOT / "memory" / "_system" / "eve_tool_map.yaml"
REPORT = ROOT / "memory" / "_reports" / "stage2_tool_map_created.md"


GROUPS = {
    "communication": {
        "telegram_bridge": ("scripts/check_telegram_bridge.py", "Telegram bridge status and runtime interface", "high"),
        "webui": ("app/eve_web.py", "Local Web UI", "high"),
        "terminal": ("app/eve_codex.py", "Local terminal/runtime ask entrypoint", "medium"),
    },
    "memory": {
        "daily_rollover": ("scripts/daily_memory_rollover.py", "Daily memory processing", "high"),
        "daily_memory_status": ("scripts/daily_memory_status.py", "Memory status read-only", "low"),
        "vector_memory_status": ("scripts/vector_memory_status.py", "Vector DB status read-only", "low"),
        "memory_query_vector": ("scripts/memory_query_vector.py", "Vector memory query", "low"),
        "memory_importer": ("scripts/memory_importer.py", "Import local memory chunks", "medium"),
        "terminal_memory_prompt_preview": ("scripts/terminal_memory_prompt_preview.py", "Preview prompt context", "low"),
    },
    "awareness": {
        "awareness_status": ("scripts/awareness_status.py", "Self-awareness status", "low"),
        "awareness_snapshot": ("scripts/awareness_snapshot.py", "Write awareness snapshot", "low"),
        "awareness_healthcheck": ("scripts/awareness_healthcheck.py", "Awareness healthcheck", "low"),
        "awareness_file_scan": ("scripts/awareness_file_scan.py", "File change scan", "low"),
        "heartbeat_once": ("scripts/heartbeat_once.py", "Write one heartbeat", "low"),
        "startup_awareness_event": ("scripts/startup_awareness_event.py", "Record startup event", "low"),
        "shutdown_awareness_event": ("scripts/shutdown_awareness_event.py", "Record shutdown event", "low"),
        "awareness_watchdog": ("scripts/awareness_watchdog.py", "Prepared watchdog, disabled by policy", "medium"),
    },
    "scheduler": {
        "install_daily_memory_rollover_task": ("scripts/install_daily_memory_rollover_task.ps1", "Install rollover task", "critical"),
        "uninstall_daily_memory_rollover_task": ("scripts/uninstall_daily_memory_rollover_task.ps1", "Remove rollover task", "critical"),
        "install_eve_pc2_startup_task": ("scripts/install_eve_pc2_startup_task.ps1", "Install Eve startup task", "critical"),
        "install_telegram_bridge_task": ("scripts/install_telegram_bridge_task.ps1", "Install Telegram startup task", "critical"),
    },
    "runtime": {
        "start_eve_pc2": ("scripts/start_eve_pc2.ps1", "Start PC2 runtime", "high"),
        "stop_eve_pc2": ("scripts/stop_eve_pc2.ps1", "Stop PC2 runtime", "high"),
        "start_telegram_bridge": ("scripts/start_telegram_bridge.ps1", "Start Telegram bridge", "high"),
        "stop_telegram_bridge": ("scripts/stop_telegram_bridge.ps1", "Stop Telegram bridge", "high"),
        "check_telegram_bridge": ("scripts/check_telegram_bridge.py", "Check Telegram bridge", "low"),
    },
    "publishing": {
        "x_posting": ("tools/x_human.py", "External X publishing", "critical"),
        "x_scheduled_posts": ("tools/x_scheduled_posts.py", "Scheduled X posts", "critical"),
    },
    "self_improvement": {
        "stage2_self_improvement_test": ("scripts/stage2_self_improvement_test.py", "Stage 2 sandbox test", "low"),
        "self_edit_request": ("scripts/self_edit_request.py", "Controlled self-edit request", "low"),
        "self_edit_rollback": ("scripts/self_edit_rollback.py", "Rollback a self-edit", "medium"),
        "permission_manager": ("core/permission_manager.py", "Scoped permission manager", "medium"),
    },
    "computer_use": {
        "screen_awareness": ("memory/_reports/screen_awareness_future_design.md", "Screen awareness design only", "high"),
        "ui_automation": ("computer/uia_executor.py", "Windows UI Automation", "high"),
        "screenshot": ("computer/screen_capture.py", "Screenshot capture", "high"),
        "ocr": ("computer/ocr.py", "OCR fallback", "medium"),
    },
}


def status_for(path: str) -> str:
    if (ROOT / path).exists():
        return "available"
    return "missing"


def tool_yaml(group: str, tool_id: str, path: str, description: str, risk: str) -> str:
    low = risk == "low"
    forbidden = risk == "critical" and tool_id in {"x_posting", "x_scheduled_posts"}
    return f"""  {tool_id}:
    command: "{path}"
    path: "{path}"
    description: "{description}"
    status: "{status_for(path)}"
    risk: "{risk}"
    allowed_without_confirmation: {str(low).lower()}
    requires_confirmation: {str(not low).lower()}
    requires_codex: {str(risk in {"high", "critical"}).lower()}
    dry_run_required: {str(risk in {"medium", "high", "critical"}).lower()}
    logs_to: "memory/transcripts/tools"
    transcript_channel: "tools"
    forbidden: {str(forbidden).lower()}
"""


def main() -> int:
    TOOL_MAP.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Generated Eve tool map for Stage 2 controlled self-improvement.", "tools:"]
    total = 0
    available = 0
    for group, tools in GROUPS.items():
        lines.append(f"  {group}:")
        for tool_id, (path, desc, risk) in tools.items():
            total += 1
            if status_for(path) == "available":
                available += 1
            lines.append(tool_yaml(group, tool_id, path, desc, risk).rstrip())
    TOOL_MAP.write_text("\n".join(lines) + "\n", encoding="utf-8")
    REPORT.write_text(f"# Stage 2 Tool Map Created\n\nTools inventoried: {total}\nAvailable/prepared: {available}\nMap: `{TOOL_MAP}`\n", encoding="utf-8")
    print(json.dumps({"ok": True, "tool_map": str(TOOL_MAP), "tools": total, "available": available}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

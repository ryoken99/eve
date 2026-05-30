from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEMORY_RUNTIME = ROOT / "memory" / "runtime"
CAP_DIR = MEMORY_RUNTIME / "capabilities"
REPORTS = ROOT / "memory" / "_reports"


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def ps_json(command: str) -> Any:
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        return json.loads(proc.stdout)
    except Exception:
        return None


def capability(capability_id: str, name: str, category: str, evidence: list[str], risk: str, notes: str = "") -> dict[str, Any]:
    present = [item for item in evidence if item.startswith("task:") or exists(item)]
    status = "available" if present else "missing"
    if capability_id in {"webui", "telegram", "terminal", "daily_rollover", "awareness"} and present:
        status = "active"
    if "prepared" in notes.lower() and present:
        status = "prepared"
    return {
        "capability_id": capability_id,
        "name": name,
        "category": category,
        "status": status,
        "evidence": evidence,
        "risk": risk,
        "can_eve_use_without_confirmation": risk == "low",
        "requires_sandro_confirmation": risk in {"medium", "high", "critical"},
        "requires_codex": risk in {"high", "critical"},
        "notes": notes,
    }


def scheduled_task_caps() -> list[dict[str, Any]]:
    raw = ps_json("Get-ScheduledTask | Where-Object {$_.TaskName -match '^Eve'} | Select-Object TaskName,State,TaskPath | ConvertTo-Json -Depth 3")
    rows = raw if isinstance(raw, list) else ([raw] if isinstance(raw, dict) else [])
    caps = []
    for row in rows:
        caps.append(
            capability(
                f"windows_task_{row.get('TaskName')}",
                row.get("TaskName", "Eve Windows Task"),
                "scheduler",
                [f"task:{row.get('TaskName')}"],
                "critical" if "Startup" in row.get("TaskName", "") else "high",
                f"Windows task state: {row.get('State')}",
            )
        )
    return caps


def build_inventory() -> dict[str, Any]:
    caps = [
        capability("terminal", "Terminal channel", "communication", ["app/eve_codex.py", "eve.ps1"], "medium"),
        capability("webui", "Web UI channel", "communication", ["app/eve_web.py", "scripts/start_eve_pc2.ps1"], "high"),
        capability("telegram", "Telegram Bridge", "communication", ["tools/telegram_bridge.py", "scripts/check_telegram_bridge.py"], "high"),
        capability("memory_retrieval", "Local memory retrieval", "memory", ["core/memory_retrieval.py"], "medium"),
        capability("vector_db", "Local Chroma vector DB", "memory", ["memory/vector/chroma", "scripts/vector_memory_status.py"], "medium"),
        capability("identity_cards", "Identity cards", "memory", ["memory/long_term/_identity_cards", "scripts/index_identity_cards.py"], "medium"),
        capability("daily_rollover", "Daily memory rollover", "memory", ["scripts/daily_memory_rollover.py"], "high"),
        capability("session_handoff", "Session handoff and rollover", "memory", ["core/session_rollover_context.py", "memory/runtime/sessions/state/current_session.json"], "medium"),
        capability("awareness", "Operational self-awareness", "awareness", ["core/awareness_engine.py", "scripts/awareness_status.py"], "medium"),
        capability("transcripts", "Per-channel transcripts", "memory", ["core/transcript_writer.py", "memory/transcripts"], "medium"),
        capability("x_posting", "X posting", "publishing", ["tools/x_human.py"], "critical"),
        capability("online_research", "Online research", "research", ["tools/web_research.py", "research/technology_watcher.py"], "medium"),
        capability("computer_use", "Computer use/UI/OCR", "tool", ["computer/uia_observer.py", "computer/uia_executor.py", "computer/ocr.py", "tools/browser_playwright.py"], "high"),
        capability("awareness_watchdog", "Awareness watchdog", "awareness", ["scripts/awareness_watchdog.py"], "medium", "Prepared but disabled until authorized."),
        capability("stage2_self_edit", "Stage 2 controlled self-edit", "self_edit", ["scripts/stage2_self_improvement_test.py", "memory/_system/stage2_self_improvement_policy.yaml"], "low"),
        capability("arsi", "ARSI controlled improvement", "self_edit", ["self_improvement/arsi_cycle.py", "self_improvement/verified_self_update.py"], "high"),
    ]
    caps.extend(scheduled_task_caps())
    return {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "capabilities": caps,
        "summary": {
            "total": len(caps),
            "active": sum(1 for cap in caps if cap["status"] == "active"),
            "available": sum(1 for cap in caps if cap["status"] == "available"),
            "prepared": sum(1 for cap in caps if cap["status"] == "prepared"),
            "missing": sum(1 for cap in caps if cap["status"] == "missing"),
        },
    }


def write_markdown(inventory: dict[str, Any]) -> Path:
    path = CAP_DIR / "capability_inventory.md"
    lines = ["# Eve Capability Inventory", "", f"Created: {inventory['created_at']}", ""]
    lines.append("| Capability | Category | Status | Risk | Evidence | Notes |")
    lines.append("|---|---|---|---|---|---|")
    for cap in inventory["capabilities"]:
        lines.append(
            f"| {cap['name']} | {cap['category']} | {cap['status']} | {cap['risk']} | {', '.join(cap['evidence'])} | {cap['notes']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    CAP_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory()
    json_path = CAP_DIR / "capability_inventory.json"
    json_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path = write_markdown(inventory)
    report = REPORTS / "stage2_capability_inventory.md"
    report.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(json.dumps({"ok": True, "json": str(json_path), "markdown": str(md_path), "summary": inventory["summary"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

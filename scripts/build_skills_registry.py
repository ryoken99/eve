from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVE_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = EVE_ROOT / "memory" / "procedural" / "skills" / "skills_registry.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def skill(
    skill_id: str,
    name: str,
    description: str,
    script_path: str,
    when_to_use: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    risk_level: str = "low",
    requires_approval: bool = False,
    status: str = "known",
    notes: str = "",
) -> dict[str, Any]:
    return {
        "skill_id": skill_id,
        "name": name,
        "description": description,
        "script_path": script_path,
        "when_to_use": when_to_use,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "risk_level": risk_level,
        "requires_approval": requires_approval,
        "last_tested_at": None,
        "status": status,
        "notes": notes,
    }


def build_registry() -> dict[str, Any]:
    skills = [
        skill("start_eve_pc2", "Start Eve PC2", "Start Eve local runtime services.", "scripts/start_eve_pc2.ps1", "When Sandro wants to start Eve on PC2.", risk_level="high", requires_approval=True),
        skill("stop_eve_pc2", "Stop Eve PC2", "Stop Eve local runtime services.", "scripts/stop_eve_pc2.ps1", "When Sandro wants to stop Eve on PC2.", risk_level="high", requires_approval=True),
        skill("status_eve_pc2", "Status Eve PC2", "Show operational status.", "scripts/awareness_status.py", "When checking Eve runtime state.", outputs=["status"], status="tested"),
        skill("check_telegram_bridge", "Check Telegram Bridge", "Check Telegram bridge process/status.", "scripts/check_telegram_bridge.py", "When checking Telegram connectivity.", outputs=["telegram status"]),
        skill("start_telegram_bridge", "Start Telegram Bridge", "Start Telegram bridge.", "scripts/start_telegram_bridge.ps1", "When Telegram bridge should start.", risk_level="high", requires_approval=True),
        skill("stop_telegram_bridge", "Stop Telegram Bridge", "Stop Telegram bridge.", "scripts/stop_telegram_bridge.ps1", "When Telegram bridge should stop.", risk_level="high", requires_approval=True),
        skill("memory_importer", "Memory Importer", "Chunk imported source memories.", "scripts/memory_importer.py", "When importing V1-V7 source memory.", inputs=["source memory files"], outputs=["chunks jsonl"], risk_level="medium", requires_approval=True),
        skill("build_vector_memory", "Build Vector Memory", "Build Chroma vector memory from chunks.", "scripts/build_vector_memory.py", "Only when explicitly rebuilding vector DB.", risk_level="high", requires_approval=True),
        skill("update_vector_memory_incremental", "Update Vector Memory Incremental", "Index new chunks without rebuilding all memory.", "scripts/update_vector_memory_incremental.py", "When new chunks are ready.", inputs=["chunks jsonl"], outputs=["Chroma update"], risk_level="medium", requires_approval=False),
        skill("memory_query_vector", "Memory Query Vector", "Search local vector memory.", "scripts/memory_query_vector.py", "When checking semantic memory.", inputs=["query"], outputs=["matches"], status="tested"),
        skill("terminal_memory_prompt_preview", "Terminal Prompt Preview", "Preview memory/context prompt for terminal.", "scripts/terminal_memory_prompt_preview.py", "When debugging prompt context.", inputs=["message"], outputs=["prompt preview"]),
        skill("daily_memory_rollover", "Daily Memory Rollover", "Close daily memory and update rollups/chunks/vector DB.", "scripts/daily_memory_rollover.py", "At midnight or controlled manual test.", risk_level="medium", requires_approval=False),
        skill("daily_memory_status", "Daily Memory Status", "Show daily memory status.", "scripts/daily_memory_status.py", "When checking rollover outputs.", outputs=["daily status"], status="tested"),
        skill("clear_memory_day_override", "Clear Memory Day Override", "Clear forced rollover memory-day override.", "scripts/clear_memory_day_override.ps1", "After controlled rollover test.", risk_level="medium", requires_approval=True),
        skill("transcript_writer", "Transcript Writer", "Write channel transcripts locally.", "core/transcript_writer.py", "When recording terminal/Telegram/Web UI/tools/errors/system.", outputs=["jsonl transcript"]),
        skill("telegram_notify", "Telegram Notify", "Send Telegram notifications.", "tools/telegram_bridge.py", "When Sandro approved Telegram communication.", risk_level="high", requires_approval=True),
        skill("create_codex_instruction", "Create Codex Instruction", "Generate Codex-ready task from candidate.", "scripts/generate_codex_task_from_candidate.py", "When a proposed improvement should be handed to Codex.", inputs=["candidate_id"], outputs=["codex task markdown"]),
    ]
    return {"version": 1, "updated_at": now_iso(), "skills": skills}


def main() -> int:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = build_registry()
    REGISTRY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "path": str(REGISTRY_PATH), "skills": len(payload["skills"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

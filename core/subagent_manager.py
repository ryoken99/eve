from __future__ import annotations

import json
from typing import Any

from core.paths import EVE_ROOT
from tools.process_manager import start_process, list_processes


def spawn_subagent(goal: str, *, role: str = "worker", context: str = "") -> dict[str, Any]:
    prompt = (
        f"Subagente Eve ({role}). Objetivo: {goal}\n\n"
        f"Contexto:\n{context}\n\n"
        "Trabalha de forma limitada e devolve resumo objetivo."
    )
    escaped = json.dumps(prompt)
    command = f"python -m app.eve_codex ask --speaker codex {escaped}"
    process = start_process(command, cwd=str(EVE_ROOT))
    return {"subagent_id": process["id"], "role": role, "goal": goal, "process": process}


def list_subagents() -> list[dict[str, Any]]:
    return [item for item in list_processes() if "app.eve_codex ask --speaker codex" in item.get("command", "")]


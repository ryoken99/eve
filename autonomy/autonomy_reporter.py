from __future__ import annotations

from datetime import datetime
from pathlib import Path

from autonomy.autonomous_executor import execute_autonomous_backlog
from autonomy.autonomy_director import run_autonomy_cycle
from core.paths import LOGS_DIR, ensure_project_dirs
from tools.interface_bus import publish_interface_message


def _report_path(cycle_name: str) -> Path:
    ensure_project_dirs()
    folder = LOGS_DIR / "autonomy" / "reports"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in cycle_name.lower()).strip("_") or "cycle"
    return folder / f"{stamp}_{safe}.md"


def build_summary(cycle: dict, execution: dict) -> str:
    decision = cycle.get("token_decision") or {}
    created = cycle.get("created_missions") or []
    executed = execution.get("executed") or []
    skipped = execution.get("skipped") or []
    token_cost = "estimativa 0" if not cycle.get("llm_called") else "GPT chamado; custo depende do tamanho do prompt/resposta"

    mission_lines = "\n".join(f"- criada: {item['objective']} ({item['status']})" for item in created) or "- nenhuma missão nova criada"
    executed_lines = "\n".join(f"- executada: {item['objective']} -> {item['result']}" for item in executed) or "- nenhuma missão executada"
    skipped_lines = "\n".join(f"- bloqueada/ignorada: {item.get('id')} ({item.get('reason')})" for item in skipped) or "- nenhum bloqueio relevante"

    return (
        "Mestre, fiz um ciclo autónomo real.\n\n"
        f"Token Gate: {'chamou GPT' if cycle.get('llm_called') else 'não chamou GPT'}.\n"
        f"Motivo: {decision.get('reason', 'sem decisão registada')}.\n"
        f"Tokens gastos: {token_cost}.\n\n"
        f"Missões:\n{mission_lines}\n\n"
        f"Execução:\n{executed_lines}\n\n"
        f"Bloqueios:\n{skipped_lines}\n\n"
        "Próximo passo: melhorar os critérios por tipo de missão e mostrar esta decisão sempre que eu agir sozinha."
    )


def run_autonomy_report_cycle(
    *,
    cycle_name: str = "autonomy_report",
    call_llm: bool | str = "auto",
    max_new_missions: int = 1,
    execute_max: int = 1,
    notify_chat: bool = True,
) -> dict:
    cycle = run_autonomy_cycle(
        triggers=["manual", "report"],
        max_new_missions=max_new_missions,
        call_llm=call_llm,
        cycle_name=cycle_name,
    )
    execution = execute_autonomous_backlog(max_missions=execute_max, notify_chat=notify_chat)
    summary = build_summary(cycle, execution)
    path = _report_path(cycle_name)
    path.write_text(
        "# Autonomy Cycle Report\n\n"
        f"Created: {datetime.now().isoformat(timespec='seconds')}\n\n"
        f"{summary}\n",
        encoding="utf-8",
    )
    if notify_chat:
        publish_interface_message("Eve", summary + f"\n\nRelatório: {path}", target="Sandro", tags=["autonomous", "report"])
    return {
        "status": "ok",
        "cycle": cycle,
        "execution": execution,
        "summary": summary,
        "report_path": str(path),
    }

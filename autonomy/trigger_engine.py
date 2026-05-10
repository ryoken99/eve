from __future__ import annotations

from typing import Any

from core.mission_control import create_mission
from memory.errors.error_memory import recent_errors
from security.audit_log import log_event


def discover_triggers() -> list[dict[str, Any]]:
    triggers: list[dict[str, Any]] = []
    errors = recent_errors(limit=8)
    if errors:
        triggers.append(
            {
                "kind": "error_repair",
                "risk": "low",
                "reason": f"{len(errors)} erros recentes encontrados.",
                "objective": "Rever erros recentes e propor correcao segura.",
                "plan": ["Agrupar erros", "Encontrar repeticoes", "Criar licao ou proposta de patch"],
            }
        )
    triggers.append(
        {
            "kind": "memory_review",
            "risk": "low",
            "reason": "Revisao periodica para manter continuidade.",
            "objective": "Rever memoria ativa e detectar contradicoes ou lacunas.",
            "plan": ["Ler contexto", "Listar lacunas", "Criar nota de memoria"],
        }
    )
    triggers.append(
        {
            "kind": "curiosity_research",
            "risk": "low",
            "reason": "Pesquisa tecnica recorrente para evolucao da Eve.",
            "objective": "Pesquisar uma melhoria tecnica aplicavel a Eve.",
            "plan": ["Escolher tema", "Pesquisar", "Enviar para lab se util"],
        }
    )
    triggers.append(
        {
            "kind": "capability_review",
            "risk": "low",
            "reason": "Roadmap dos 17 pontos deve guiar melhorias autonomas.",
            "objective": "Rever os 17 pontos da Eve e criar proxima melhoria segura.",
            "plan": ["Auditar pontos", "Escolher lacuna", "Criar candidato no lab"],
        }
    )
    return triggers


def create_missions_from_triggers(*, max_new: int = 2) -> dict[str, Any]:
    created = []
    for trigger in discover_triggers()[:max_new]:
        mission = create_mission(
            trigger["objective"],
            plan=trigger["plan"],
            permissions=["read_memory", "write_memory"],
            status="proposed",
            source=f"trigger:{trigger['kind']}",
        )
        created.append({"trigger": trigger, "mission": mission})
    result = {"created": [{"id": item["mission"]["id"], "kind": item["trigger"]["kind"]} for item in created]}
    log_event("trigger_engine_created_missions", result)
    return result

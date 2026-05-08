from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from core.mission_control import create_mission, list_missions
from core.paths import EVE_ROOT, LOGS_DIR, ensure_project_dirs
from memory.errors.error_memory import recent_errors
from autonomy.token_gate import decide_llm_call, record_llm_call


SENSITIVE_BOUNDARY = (
    "Nao executes acoes sensiveis: externas, destrutivas, privadas, financeiras, admin, "
    "credenciais, publicacao/envio, apagamento, ou self-modify aplicado sem aprovacao explicita do Sandro."
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def autonomy_log_path() -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "autonomy"
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"


def log_autonomy_event(event: str, payload: dict) -> Path:
    row = {"timestamp": now_iso(), "event": event, **payload}
    path = autonomy_log_path()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def active_or_proposed_missions() -> list[dict]:
    return [
        mission
        for mission in list_missions()
        if mission.get("status") in {"draft", "proposed", "running", "paused", "blocked"}
    ]


def generate_impulses(triggers: list[str] | None = None) -> list[dict]:
    triggers = triggers or []
    impulses: list[dict] = []
    errors = recent_errors(limit=5)
    if errors:
        impulses.append(
            {
                "kind": "error_review",
                "title": "Rever erros recentes e criar licoes",
                "reason": f"Foram encontrados {len(errors)} erros recentes.",
                "risk": "low",
                "plan": [
                    "Ler erros recentes",
                    "Agrupar falhas repetidas",
                    "Criar proposta de melhoria ou licao adaptativa",
                ],
                "permissions": ["read_memory", "write_memory"],
            }
        )
    if "no_active_work" in triggers or not active_or_proposed_missions():
        impulses.extend(
            [
                {
                    "kind": "self_review",
                    "title": "Autoavaliacao diaria da Eve",
                    "reason": "Nao ha trabalho ativo suficiente; criar reflexao operacional de baixo risco.",
                    "risk": "low",
                    "plan": [
                        "Rever missoes, logs e capacidades recentes",
                        "Identificar 3 pontos fortes e 3 falhas",
                        "Criar propostas de melhoria sem alterar core",
                    ],
                    "permissions": ["read_memory", "write_memory"],
                },
                {
                    "kind": "memory_hygiene",
                    "title": "Rever memoria viva e contradicoes",
                    "reason": "Memoria precisa de curadoria continua para evitar factos antigos ou contraditorios.",
                    "risk": "low",
                    "plan": [
                        "Ler memorias recentes e longas",
                        "Marcar candidatos a conflito ou baixa confianca",
                        "Propor consolidacao sem apagar informacao",
                    ],
                    "permissions": ["read_memory", "write_memory"],
                },
                {
                    "kind": "research_reflection",
                    "title": "Pesquisar melhoria tecnica para a Eve",
                    "reason": "RSI controlado precisa de pesquisa e planos antes de qualquer alteracao.",
                    "risk": "low",
                    "plan": [
                        "Escolher tema tecnico relevante",
                        "Criar research report auditavel",
                        "Gerar proposta de melhoria para aprovacao",
                    ],
                    "permissions": ["control_browser", "read_memory", "write_memory"],
                },
            ]
        )
    return impulses


def build_autonomy_prompt(impulses: list[dict], *, cycle_name: str) -> str:
    return (
        f"Ciclo autonomo da Eve: {cycle_name}\n"
        f"{SENSITIVE_BOUNDARY}\n\n"
        "Analisa os impulsos abaixo e devolve uma revisao curta com:\n"
        "1. quais devem virar missoes propostas,\n"
        "2. qual exige aprovacao,\n"
        "3. qual e o proximo passo seguro.\n\n"
        f"Impulsos:\n{json.dumps(impulses, indent=2, ensure_ascii=False)}"
    )


def call_codex_llm(prompt: str, *, timeout: int = 180) -> dict:
    command = [
        sys.executable,
        str(EVE_ROOT / "app" / "eve_codex.py"),
        "ask",
        "--speaker",
        "codex",
        prompt,
    ]
    completed = subprocess.run(command, cwd=str(EVE_ROOT), text=True, capture_output=True, timeout=timeout)
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-8000:],
        "stderr": completed.stderr[-4000:],
    }


def create_mission_from_impulse(impulse: dict, *, cycle_name: str) -> dict:
    mission = create_mission(
        impulse["title"],
        plan=impulse.get("plan") or [],
        permissions=impulse.get("permissions") or [],
        status="proposed",
        source=f"autonomy:{cycle_name}:{impulse['kind']}",
    )
    mission["risk"] = impulse.get("risk", "unknown")
    mission["impulse_reason"] = impulse.get("reason", "")
    return mission


def run_autonomy_cycle(
    *,
    triggers: list[str] | None = None,
    max_new_missions: int = 3,
    call_llm: bool | str = False,
    cycle_name: str = "daily_self_review",
) -> dict:
    ensure_project_dirs()
    impulses = generate_impulses(triggers)
    errors = recent_errors(limit=10)
    created = []
    for impulse in impulses[: max(0, max_new_missions)]:
        if impulse.get("risk") != "low":
            continue
        created.append(create_mission_from_impulse(impulse, cycle_name=cycle_name))

    token_decision = decide_llm_call({"impulses": impulses, "recent_errors": errors}) if call_llm == "auto" else {
        "should_call_llm": bool(call_llm),
        "reason": "chamada LLM pedida explicitamente" if call_llm else "LLM desativado neste ciclo",
        "prompt_type": "explicit_review" if call_llm else "none",
        "risk": "low",
        "budget_ok": True,
        "cooldown_ok": True,
    }

    llm_result = None
    if token_decision["should_call_llm"] and impulses:
        llm_result = call_codex_llm(build_autonomy_prompt(impulses, cycle_name=cycle_name))
        record_llm_call(cycle_name, token_decision, result=llm_result)

    result = {
        "status": "ok",
        "cycle": cycle_name,
        "timestamp": now_iso(),
        "boundary": SENSITIVE_BOUNDARY,
        "impulses": impulses,
        "created_missions": [
            {
                "id": mission["id"],
                "objective": mission["objective"],
                "status": mission["status"],
                "risk": mission.get("risk", "low"),
                "next_step": mission.get("next_step"),
            }
            for mission in created
        ],
        "token_decision": token_decision,
        "llm_called": bool(llm_result),
        "llm_result": llm_result,
    }
    log_autonomy_event("autonomy_cycle", result)
    return result

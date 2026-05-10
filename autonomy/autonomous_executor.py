from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from core.mission_control import add_checkpoint, append_mission_log, list_missions, load_mission, set_mission_status, update_step
from core.paths import MEMORY_DIR, ensure_project_dirs
from core.self_report import functional_self_report
from autonomy.capability_roadmap import capability_audit, write_capability_audit
from lab.lab_manager import create_candidate
from memory.errors.error_memory import recent_errors
from memory.memory_manager import context_bundle
from research.research_notes import append_technology_learning
from tools.interface_bus import publish_interface_message


ALLOWED_AUTONOMOUS_KINDS = {"error_review", "self_review", "memory_hygiene", "research_reflection", "capability_improvement"}


def mission_kind(mission: dict) -> str:
    source = mission.get("source", "")
    if source.startswith("autonomy:"):
        return source.rsplit(":", 1)[-1]
    return ""


def _append_report(relative_path: str, title: str, body: str) -> Path:
    ensure_project_dirs()
    path = MEMORY_DIR / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().isoformat(timespec="seconds")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n# {title}\n\nCreated: {stamp}\n\n{body.strip()}\n")
    return path


def _complete_steps(mission_id: str, mission: dict, note: str) -> None:
    for step in mission.get("steps", []):
        if step.get("status") not in {"done", "skipped"}:
            update_step(mission_id, int(step["index"]), "done", note=note, actor="eve_autonomy")


def _error_review() -> dict:
    errors = recent_errors(limit=10)
    if not errors:
        summary = "Nao encontrei erros recentes para rever."
        path = _append_report("errors/autonomous_error_review.md", "Autonomous Error Review", summary)
        return {"summary": summary, "path": str(path), "count": 0}
    rows = []
    for err in errors:
        rows.append(f"- {err.get('timestamp')} [{err.get('source')}] {err.get('error_type')}: {err.get('error_text', '')[:250]}")
    body = "Erros revistos:\n" + "\n".join(rows) + "\n\nProximo passo seguro: criar licoes adaptativas para erros repetidos antes de mexer no core."
    path = _append_report("errors/autonomous_error_review.md", "Autonomous Error Review", body)
    return {"summary": f"Revistos {len(errors)} erros recentes e registado relatorio.", "path": str(path), "count": len(errors)}


def _self_review() -> dict:
    report = functional_self_report("autonomous_self_review")
    body = json.dumps(report, indent=2, ensure_ascii=False)
    path = _append_report("dream_reports/autonomous_self_review.md", "Autonomous Self Review", body)
    return {"summary": "Fiz uma autoavaliacao operacional e registei o relatorio.", "path": str(path)}


def _memory_hygiene() -> dict:
    bundle = context_bundle(6000)
    body = (
        "Amostra de memoria revista para higiene.\n\n"
        "Observacao: esta versao ainda nao altera nem apaga memoria; apenas cria nota de curadoria.\n\n"
        f"Contexto analisado:\n{bundle[:4000]}"
    )
    path = _append_report("medium_term/memory_hygiene_notes.md", "Autonomous Memory Hygiene", body)
    return {"summary": "Revisei uma amostra de memoria e registei nota de higiene sem apagar nada.", "path": str(path)}


def _research_reflection() -> dict:
    text = (
        "Autonomous reflection: a Eve quer melhorar a validacao cruzada de claims em research reports, "
        "marcando cada ponto como confirmado por 1 fonte, multiplas fontes, inferido ou incerto."
    )
    path = append_technology_learning(text)
    return {"summary": "Registei uma reflexao tecnica de baixo risco para proxima melhoria de research.", "path": str(path)}


def _capability_improvement() -> dict:
    audit_path = write_capability_audit()
    audit = capability_audit()
    target = audit["weakest"][0]
    title = f"Capability {target['id']} - {target['title']}"
    hypothesis = (
        f"Melhorar o ponto {target['id']} aumenta a aproximacao da Eve ao objetivo do Sandro. "
        f"Estado atual: {target['status']} / {target['maturity']}. Objetivo: {target['desired']}."
    )
    candidate = create_candidate(title, hypothesis, metric="capability_roadmap_score")
    body = (
        f"Auditoria guardada: {audit_path}\n"
        f"Candidato criado no lab: {candidate}\n"
        f"Ponto escolhido: {target['id']} - {target['title']}\n"
        f"Proxima acao segura: desenhar patch pequeno e testavel antes de alterar core."
    )
    path = _append_report("medium_term/autonomous_capability_improvements.md", "Autonomous Capability Improvement", body)
    return {
        "summary": f"Auditei os 17 pontos e criei candidato de lab para o ponto {target['id']}.",
        "path": str(path),
        "audit": str(audit_path),
        "candidate": str(candidate),
    }


def _run_handler(kind: str) -> dict:
    if kind == "error_review":
        return _error_review()
    if kind == "self_review":
        return _self_review()
    if kind == "memory_hygiene":
        return _memory_hygiene()
    if kind == "research_reflection":
        return _research_reflection()
    if kind == "capability_improvement":
        return _capability_improvement()
    raise ValueError(f"tipo autonomo nao suportado: {kind}")


def execute_autonomous_mission(mission_id: str, *, notify_chat: bool = True) -> dict:
    mission = load_mission(mission_id)
    kind = mission_kind(mission)
    if kind not in ALLOWED_AUTONOMOUS_KINDS:
        set_mission_status(mission_id, "blocked", reason="Missao fora da lista autonoma de baixo risco.", actor="eve_autonomy")
        return {"status": "blocked", "reason": "unsupported_autonomous_kind", "kind": kind}
    if mission.get("status") not in {"proposed", "draft", "paused", "blocked"}:
        return {"status": "skipped", "reason": f"estado nao executavel: {mission.get('status')}", "kind": kind}

    set_mission_status(mission_id, "running", reason=f"Execucao autonoma iniciada: {kind}", actor="eve_autonomy")
    append_mission_log(mission_id, "eve_autonomy", "A executar missao autonoma de baixo risco.", data={"kind": kind})
    output = _run_handler(kind)
    refreshed = load_mission(mission_id)
    _complete_steps(mission_id, refreshed, output["summary"])
    add_checkpoint(mission_id, "autonomous_execution_result", output)
    set_mission_status(mission_id, "done", reason=output["summary"], actor="eve_autonomy")

    chat_message = (
        f"Mestre, executei autonomamente uma missao de baixo risco: {mission['objective']}.\n"
        f"Resultado: {output['summary']}\n"
        f"Registo: {output.get('path', 'sem ficheiro')}"
    )
    entry = publish_interface_message("Eve", chat_message, target="Sandro", tags=["autonomous", kind]) if notify_chat else None
    return {"status": "done", "kind": kind, "output": output, "chat_message": entry}


def execute_autonomous_backlog(*, max_missions: int = 2, notify_chat: bool = True) -> dict:
    executed = []
    skipped = []
    for item in list_missions(status="proposed"):
        if len(executed) >= max_missions:
            break
        mission = load_mission(item["id"])
        if mission_kind(mission) not in ALLOWED_AUTONOMOUS_KINDS:
            skipped.append({"id": mission["id"], "reason": "unsupported_kind"})
            continue
        result = execute_autonomous_mission(mission["id"], notify_chat=notify_chat)
        executed.append({"id": mission["id"], "objective": mission["objective"], "result": result["status"]})
    return {"executed": executed, "skipped": skipped}

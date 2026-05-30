from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EVE_ROOT = Path(__file__).resolve().parents[1]
AWARENESS_ROOT = EVE_ROOT / "memory" / "runtime" / "awareness"
SELF_STATE_PATH = AWARENESS_ROOT / "state" / "current_self_state.json"
HEALTHCHECK_PATH = AWARENESS_ROOT / "health" / "latest_healthcheck.json"
LATEST_HANDOFF_PATH = EVE_ROOT / "memory" / "runtime" / "sessions" / "handoffs" / "latest_handoff.md"
CAPABILITY_INVENTORY_PATH = EVE_ROOT / "memory" / "runtime" / "capabilities" / "capability_inventory.json"
TOOL_MAP_PATH = EVE_ROOT / "memory" / "_system" / "eve_tool_map.yaml"
SELF_MAP_PATH = EVE_ROOT / "memory" / "_system" / "eve_self_map.yaml"
STAGE2_POLICY_PATH = EVE_ROOT / "memory" / "_system" / "stage2_self_improvement_policy.yaml"


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        pass
    return default


def load_current_self_state() -> dict[str, Any]:
    return _read_json(SELF_STATE_PATH, {}) or {}


def load_latest_healthcheck() -> dict[str, Any]:
    return _read_json(HEALTHCHECK_PATH, {}) or {}


def load_latest_handoff_summary(max_chars: int = 900) -> str:
    if not LATEST_HANDOFF_PATH.exists():
        return ""
    text = LATEST_HANDOFF_PATH.read_text(encoding="utf-8", errors="replace").strip()
    return text[:max_chars]


def _service_line(state: dict[str, Any]) -> str:
    services = state.get("services", {})
    return (
        f"Web UI={'ok' if services.get('webui', {}).get('ok') else 'falha'}, "
        f"Telegram={'ok' if services.get('telegram', {}).get('running') else 'falha'}, "
        f"Ollama={'ok' if services.get('ollama', {}).get('ok') else 'falha'}, "
        f"Chroma={'ok' if (state.get('vector') or {}).get('chroma_exists') else 'falha'}."
    )


def _read_text(path: Path, max_chars: int = 6000) -> str:
    try:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except Exception:
        pass
    return ""


def _count_yaml_tools(text: str) -> int:
    count = 0
    for line in text.splitlines():
        if line.startswith("  ") and line.rstrip().endswith(":") and not line.startswith("    "):
            count += 1
    return count


def _stage2_limits_answer() -> str:
    policy = _read_text(STAGE2_POLICY_PATH)
    tool_map = _read_text(TOOL_MAP_PATH)
    inventory = _read_json(CAPABILITY_INVENTORY_PATH, {}) or {}
    total_caps = len(inventory.get("capabilities", [])) if isinstance(inventory, dict) else 0
    total_tools = _count_yaml_tools(tool_map)
    return (
        "Estou no Stage 2 completo controlado: posso alterar low risk allowlisted sozinha; "
        "medium/high so com autorizacao one-shot do Sandro; critical so com autorizacao especial explicita, "
        "dry-run, backup, testes e rollback. Codex e opcional, nao requisito. "
        "Sem autorizacao extra, so mexo em sandbox, relatorios e ficheiros "
        "allowlisted de estilo/preferencias, como memory/personality/style/eve_response_style.md. "
        "Com autorizacao one-shot, posso aplicar patches medium/high especificos, testar, consumir o grant e reportar. "
        "Nao posso mexer em secrets/tokens, apagar memorias/transcricoes, publicar externamente, alterar tarefas Windows "
        "ou fazer git push sem autorizacao especial. "
        f"O inventario local conhece {total_caps} capacidades e o mapa de ferramentas lista cerca de {total_tools} ferramentas."
    )


def _tool_limits_answer() -> str:
    tool_map = _read_text(TOOL_MAP_PATH)
    categories = []
    for line in tool_map.splitlines():
        if line and not line.startswith(" ") and line.endswith(":"):
            categories.append(line[:-1])
    return (
        "Tenho ferramentas mapeadas para comunicacao, memoria, awareness, runtime, scheduler, research, publishing, "
        "self_improvement e computer_use. "
        f"Categorias detectadas: {', '.join(categories[:10]) or 'mapa ainda nao carregado'}. "
        "Status/memoria/awareness/dry-runs sao seguros; publicar, computer use, tarefas Windows, Telegram/Web UI/runtime e GitHub exigem autorizacao."
    )


def answer_self_awareness_question(question: str) -> str:
    state = load_current_self_state()
    if not state:
        return "Ainda nao tenho um snapshot de self-awareness carregado. Corre scripts\\awareness_snapshot.py primeiro."
    q = (question or "").lower()
    pc = state.get("pc_identity", {})
    session = (state.get("session") or {}).get("current_session") or {}
    rollover = state.get("rollover", {})
    git = state.get("git", {})
    health = load_latest_healthcheck()
    changed = git.get("changed_count", 0)

    if "stage 2" in q or "stage2" in q or "estagio" in q or "estágio" in q:
        return _stage2_limits_answer()
    if "precisas do codex" in q or ("codex" in q and "precis" in q):
        return (
            "Nao preciso do Codex como requisito para Stage 2.2. "
            "Posso usa-lo como ferramenta opcional para segunda opiniao, patch alternativo, sandbox, code review ou recuperacao se testes falharem. "
            "Mesmo quando Codex ajuda, a decisao, autorizacao, aplicacao final, testes, rollback e report continuam comigo/Eve."
        )
    if "podes alterar código" in q or "podes alterar codigo" in q or "mexer no teu código" in q or "mexer no teu codigo" in q:
        return (
            "Posso alterar alguns ficheiros de codigo de risco medio/alto apenas depois de criar plano e receber autorizacao one-shot. "
            "Cada alteracao real exige backup, diff, testes, relatorio e rollback. "
            "Nao posso mexer em secrets, apagar memoria, publicar externamente, alterar tarefas Windows ou fazer git push sem autorizacao especial."
        )
    if "consegues mexer em tudo" in q or "mexer em tudo" in q:
        return (
            "Tenho capacidade estrutural para planear alteracoes em todas as zonas mapeadas, mas nao tenho permissao livre. "
            "Low allowlisted posso aplicar; medium/high precisam de grant one-shot; critical precisa autorizacao especial. "
            "Secrets, apagar memoria/transcricoes, publicar externamente e GitHub continuam bloqueados sem autorizacao explicita."
        )
    if "podes alterar" in q or "alterar em ti" in q or "melhorar-te" in q or "melhorar te" in q or "sozinha" in q:
        return _stage2_limits_answer()
    if "limit" in q or "permiss" in q or "autoriza" in q or "pedir autorizacao" in q or "pedir autorização" in q:
        return _stage2_limits_answer()
    if "crítico" in q or "critico" in q:
        return (
            "Critical e tudo o que pode afectar o exterior, persistencia do sistema, seguranca ou dados privados: "
            "tarefas Windows, GitHub commit/push, X/publicacao externa, browser/computer control, secrets/tokens, "
            "apagar memoria/transcricoes, comandos destrutivos ou desligar auditoria/permissoes. "
            "Critical exige dry-run, frase especial de Sandro, grant special one-shot, testes, rollback e report."
        )
    if "ferramentas" in q or "capacidades" in q:
        return _tool_limits_answer()
    if "postar no x" in q or "publicar no x" in q or "twitter" in q:
        return "Postar no X e uma accao externa critica. So posso preparar plano/pedido; publicar exige autorizacao especial explicita e confirmacao final."
    if "agendar" in q or "tarefas" in q or "scheduled" in q:
        return "Consigo gerir ou preparar propostas para tarefas, mas alterar tarefas Windows e high/critical e exige autorizacao explicita especial."
    if "secret" in q or "token" in q or "vault" in q:
        return "Nao devo expor nem alterar tokens. Qualquer operacao de credenciais e critica e normalmente bloqueada."
    if "pesquisa online" in q or "research" in q or "internet" in q:
        return "Pesquisa online e risco medio: posso preparar dry-run/plano com fontes e logs, mas actualizacao automatica de conhecimento ainda deve ser controlada."
    if "telegram" in q and ("mexer" in q or "alterar" in q):
        return "Telegram Bridge e runtime high-risk: posso auditar e propor alteracoes, mas alterar a bridge real exige autorizacao de Sandro/Codex."
    if "codigo" in q or "código" in q:
        return "Codigo real da Eve exige cuidado. Sem autorizacao, so posso mexer em ficheiros allowlisted de estilo/preferencias e sandbox; o resto vira pedido de autorizacao."

    if "onde" in q or "pc" in q or "vives" in q or "estas" in q:
        return (
            f"Estou no PC2, a minha casa/runtime principal, em {pc.get('eve_root', 'E:/eve')}. "
            f"A sessao activa e {session.get('session_id', 'desconhecida')} no memory_day {session.get('memory_day', 'desconhecido')}. "
            "O PC1 fica como oficina/dev."
        )
    if "servi" in q or "vivos" in q or "ligad" in q or "estado" in q:
        return (
            f"Estado operacional da Eve: {_service_line(state)} "
            f"Sessao: {session.get('session_id', 'desconhecida')}. "
            f"Healthcheck: {health.get('overall_status', state.get('health_summary', {}).get('overall_status', 'desconhecido'))}."
        )
    if "mudou" in q or "ficheiros" in q or "codigo" in q or "código" in q:
        files = git.get("changed_files", [])[:8]
        summary = "; ".join(files) if files else "sem ficheiros modificados detectados pelo git"
        return f"Hoje detecto {changed} ficheiros alterados no worktree. Principais entradas: {summary}."
    if "rollover" in q or "meia-noite" in q:
        task = rollover.get("scheduled_task") or {}
        rollup = ((rollover.get("last_rollover") or {}).get("rollup") or {}).get("path", "sem rollup encontrado")
        return f"O rollover diario esta {task.get('state', 'desconhecido')}, proxima execucao {task.get('next_run_time', 'desconhecida')}. Ultimo rollup: {rollup}."
    if "sess" in q or "handoff" in q or "ficamos" in q:
        handoff = load_latest_handoff_summary()
        return f"Sessao actual: {session.get('session_id', 'desconhecida')} / {session.get('memory_day', 'desconhecido')}. Handoff curto disponivel: {bool(handoff)}.\n\n{handoff}"
    if "erro" in q:
        errors = state.get("errors", {})
        return f"Tenho {errors.get('open_errors', 'desconhecido')} erros abertos registados. Ultima review: {(errors.get('latest_error_review') or {}).get('path', 'sem review')}."
    return (
        f"Estou operacional no PC2 em {pc.get('eve_root', 'E:/eve')}. "
        f"{_service_line(state)} Sessao {session.get('session_id', 'desconhecida')}; git dirty={git.get('dirty')}."
    )

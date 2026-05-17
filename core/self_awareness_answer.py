from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EVE_ROOT = Path(__file__).resolve().parents[1]
AWARENESS_ROOT = EVE_ROOT / "memory" / "runtime" / "awareness"
SELF_STATE_PATH = AWARENESS_ROOT / "state" / "current_self_state.json"
HEALTHCHECK_PATH = AWARENESS_ROOT / "health" / "latest_healthcheck.json"
LATEST_HANDOFF_PATH = EVE_ROOT / "memory" / "runtime" / "sessions" / "handoffs" / "latest_handoff.md"


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

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InternalAction:
    key: str
    tool: str
    reason: str
    example_args: dict[str, Any]
    triggers: tuple[str, ...]

    def matches(self, text: str) -> bool:
        lowered = text.lower()
        return any(trigger in lowered for trigger in self.triggers)

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "tool": self.tool,
            "reason": self.reason,
            "example_args": self.example_args,
        }


INTERNAL_ACTIONS = [
    InternalAction(
        "long_task",
        "autonomy_cycle",
        "Pedido parece exigir trabalho longo; criar/continuar missao e executar ciclo autonomo.",
        {"cycle_name": "long_task", "call_llm": "auto", "max_new_missions": 1, "execute_max": 1, "notify_chat": True},
        ("tarefa longa", "trabalha bastante", "passo a passo", "ate acabar", "até acabar", "continua sozinho", "loop continuo"),
    ),
    InternalAction(
        "codex_eve_loop",
        "run_terminal",
        "O loop Codex-Eve existe como comando interno; usar quando o Sandro quer colaboracao Codex/Eve sem intervencao constante.",
        {"command": "python app\\eve_codex.py loop \"OBJECTIVE\" --mode 1", "cwd": "D:\\Eve", "background": True, "approved": True},
        ("loop", "sem minha intervencao", "sem eu intervir", "codex", "instrutor"),
    ),
    InternalAction(
        "session_checkpoint",
        "session_checkpoint",
        "Guardar estado antes de trocar de sessao ou antes de uma tarefa grande.",
        {"reason": "Eve decidiu guardar continuidade"},
        ("guardar contexto", "nao perder o fio", "não perder o fio", "trocar de sessao", "trocar de sessão", "handoff"),
    ),
    InternalAction(
        "session_rotate",
        "session_rotate",
        "Rodar para nova sessao quando o contexto esta grande, mantendo handoff ativo.",
        {"reason": "contexto grande; rotacao preventiva"},
        ("nova sessao", "nova sessão", "esgotar contexto", "contexto cheio", "mudar de sessao", "mudar de sessão"),
    ),
    InternalAction(
        "browser",
        "open_browser",
        "Abrir Chrome/perfil Eve diretamente; nao pedir ao Sandro para abrir manualmente.",
        {"url": "https://www.google.com"},
        ("abre o navegador", "abrir navegador", "browser", "chrome", "x.com", "site"),
    ),
    InternalAction(
        "research",
        "web_research_report",
        "Pesquisa auditavel com relatorio quando o pedido envolve pesquisar/aprender informacao externa.",
        {"query": "TOPIC", "max_pages": 8, "open_visible_browser": True},
        ("pesquisa", "research", "papers", "artigos", "internet", "vai online"),
    ),
    InternalAction(
        "memory",
        "memory_context",
        "Consultar memoria antes de responder a factos pessoais, continuidade ou identidade da Eve.",
        {"max_chars": 12000},
        ("lembras", "memoria", "memória", "quem sou", "quem és", "quem es", "sobre mim"),
    ),
    InternalAction(
        "vector",
        "vector_prefetch",
        "Usar memoria semantica quando o pedido refere algo antigo ou relacionado por significado.",
        {"query": "USER_REQUEST", "limit": 5},
        ("procura na memoria", "procura na memória", "relacionado", "antigo", "antes"),
    ),
    InternalAction(
        "terminal",
        "run_terminal",
        "Executar comando local quando o pedido pede verificar/corrigir algo no PC.",
        {"command": "COMMAND", "cwd": "D:\\Eve", "approved": True},
        ("powershell", "terminal", "comando", "verifica", "corrige", "instala"),
    ),
    InternalAction(
        "x_post",
        "schedule_repeated_x_posts",
        "Agendar/publicar no X quando o Sandro pede explicitamente post/publicacao; se forem varias publicacoes, usar batch com verificacao e autocorrecao.",
        {"count": 3, "interval_minutes": 2, "topic": "how Eve feels", "approved": True},
        ("post no x", "publica no x", "publicação no x", "tweet", "x.com", "vezes"),
    ),
    InternalAction(
        "daemon",
        "autonomy_cycle",
        "Usar ciclo autonomo/daemon para impulsos, revisao de erros, memoria e melhoria continua.",
        {"cycle_name": "autonomous_internal", "call_llm": "auto", "max_new_missions": 1, "execute_max": 1, "notify_chat": True},
        ("autonomia", "proativa", "proactivo", "impulso", "daemon", "melhoria continua", "recursive"),
    ),
]


def plan_internal_actions(prompt: str, *, limit: int = 5) -> list[dict[str, Any]]:
    matches = [action.as_dict() for action in INTERNAL_ACTIONS if action.matches(prompt)]
    return matches[:limit]


def format_internal_plan(prompt: str, *, limit: int = 5) -> str:
    actions = plan_internal_actions(prompt, limit=limit)
    if not actions:
        return "Nenhuma sugestao interna especifica; usar catalogo geral de ferramentas se necessario."
    lines = [
        "Sugestoes internas para a Eve usar sem pedir slash commands ao Sandro:",
    ]
    for action in actions:
        lines.append(f"- {action['key']} -> tool `{action['tool']}`: {action['reason']} args_exemplo={action['example_args']}")
    return "\n".join(lines)


def all_internal_actions() -> list[dict[str, Any]]:
    return [action.as_dict() for action in INTERNAL_ACTIONS]

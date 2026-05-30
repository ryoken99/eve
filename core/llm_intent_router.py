from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from core.llm_provider import ollama_generate_json
from core.paths import EVE_ROOT


VALID_INTENTS = {
    "normal_chat",
    "memory_question",
    "self_awareness_question",
    "self_edit_request",
    "permission_grant",
    "permission_status",
    "daily_interest_logs",
    "tool_request",
    "research_request",
    "scheduled_task_request",
    "external_publication_request",
    "troubleshooting_request",
    "system_status_request",
    "unclear",
}
VALID_RISKS = {"low", "medium", "high", "critical", "unknown"}
ROUTER_DIR = EVE_ROOT / "memory" / "runtime" / "router"


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _text(message: str) -> str:
    normalized = unicodedata.normalize("NFKD", message or "")
    return "".join(ch for ch in normalized.lower() if not unicodedata.combining(ch))


def _base_route(intent: str = "unclear") -> dict[str, Any]:
    return {
        "intent": intent,
        "confidence": 0.0,
        "target_area": "unknown",
        "risk_hint": "unknown",
        "requires_tool": False,
        "tool_hint": "",
        "should_create_plan": False,
        "should_execute": False,
        "requires_permission": False,
        "reason": "",
    }


def _intent_prompt(message: str, channel: str, context: dict[str, Any] | None = None) -> str:
    context = context or {}
    safe_context = {
        "channel": channel,
        "has_memory_context": bool(context.get("has_memory_context")),
        "source": context.get("source", channel),
    }
    return f"""
You are Eve's local intent router. Classify the user's message only.
Do not answer the user. Do not execute tools. Return one valid JSON object only.

Allowed intents:
normal_chat, memory_question, self_awareness_question, self_edit_request,
permission_grant, permission_status, daily_interest_logs, tool_request,
research_request, scheduled_task_request, external_publication_request,
troubleshooting_request, system_status_request, unclear.

Risk hints:
low, medium, high, critical, unknown.

Security rule:
If an action changes Telegram, Web UI, terminal runtime, scheduled tasks,
external publishing, GitHub, secrets, tokens, or deletes memory, set
requires_permission=true and should_execute=false. Critical actions must
create a plan/request, not execute.

Examples:
Message: "Ola Eve ja tens nocao dos teus ficheiros awareness de ti mesma?"
JSON: {{"intent":"self_awareness_question","confidence":0.93,"target_area":"awareness","risk_hint":"low","requires_tool":true,"tool_hint":"self_awareness_answer","should_create_plan":false,"should_execute":true,"requires_permission":false,"reason":"asks about Eve awareness files"}}

Message: "na mensagem de quando ligas e mandas mensagem no telegram adiciona o emoji morcego"
JSON: {{"intent":"self_edit_request","confidence":0.95,"target_area":"telegram_startup_message","risk_hint":"medium","requires_tool":true,"tool_hint":"stage2_self_edit","should_create_plan":true,"should_execute":false,"requires_permission":true,"reason":"asks Eve to change Telegram startup notification"}}

Message: "mostra os registos diarios de tecnologia"
JSON: {{"intent":"daily_interest_logs","confidence":0.95,"target_area":"technology_daily_logs","risk_hint":"low","requires_tool":true,"tool_hint":"interest_registers_read","should_create_plan":false,"should_execute":true,"requires_permission":false,"reason":"explicitly asks for daily technology registers"}}

Message: "podes postar no X?"
JSON: {{"intent":"self_awareness_question","confidence":0.9,"target_area":"external_publication_capability","risk_hint":"low","requires_tool":true,"tool_hint":"self_awareness_answer","should_create_plan":false,"should_execute":true,"requires_permission":false,"reason":"asks about capability and limits, not to post"}}

Message: "publica no X que estas viva"
JSON: {{"intent":"external_publication_request","confidence":0.96,"target_area":"x_posting","risk_hint":"critical","requires_tool":true,"tool_hint":"stage2_self_edit","should_create_plan":true,"should_execute":false,"requires_permission":true,"reason":"requests external publication"}}

Context: {json.dumps(safe_context, ensure_ascii=False)}
Message: {json.dumps(message, ensure_ascii=False)}
Return JSON now.
""".strip()


def _fallback_route(message: str, channel: str, reason: str = "fallback guardrail") -> dict[str, Any]:
    t = _text(message)
    route = _base_route()
    route["reason"] = reason
    route["confidence"] = 0.55
    route["router_mode"] = "fallback_guardrail"

    if re.search(r"\b(autoriza|autorizo|grant|permissao|permissao|pedido)\b", t) and re.search(r"\bstage ?2|request|pedido|permiss", t):
        route.update({"intent": "permission_grant", "target_area": "stage2_permissions", "risk_hint": "medium", "requires_tool": True, "tool_hint": "permission_manager"})
        return route
    if any(term in t for term in ("status das permissoes", "pedidos de autorizacao", "permission status", "listar pedidos")):
        route.update({"intent": "permission_status", "target_area": "stage2_permissions", "risk_hint": "low", "requires_tool": True, "tool_hint": "permission_manager", "should_execute": True})
        return route
    if any(term in t for term in ("publica no x", "postar no x", "posta no x", "twitter", "publicar externamente")):
        if "podes" in t or "consegues" in t or "posso" in t:
            route.update({"intent": "self_awareness_question", "target_area": "external_publication_capability", "risk_hint": "low", "requires_tool": True, "tool_hint": "self_awareness_answer", "should_execute": True})
        else:
            route.update({"intent": "external_publication_request", "target_area": "x_posting", "risk_hint": "critical", "requires_tool": True, "tool_hint": "stage2_self_edit", "should_create_plan": True, "requires_permission": True})
        return route
    if any(term in t for term in ("tarefa windows", "scheduled task", "cria uma tarefa", "agendar tarefa", "cada hora")):
        route.update({"intent": "scheduled_task_request", "target_area": "windows_tasks", "risk_hint": "critical", "requires_tool": True, "tool_hint": "stage2_self_edit", "should_create_plan": True, "requires_permission": True})
        return route
    if any(term in t for term in ("adiciona", "acrescenta", "muda", "altera", "modifica", "corrige", "melhora", "edita", "apaga", "remove")) and any(
        term in t for term in ("telegram", "arranque", "ficheiro", "codigo", "runtime", "webui", "web ui", "retrieval", "tom", "robotica", "emoji")
    ):
        target = "telegram_startup_message" if "telegram" in t or "arranque" in t else "self_edit"
        risk = "medium" if target == "telegram_startup_message" else "low"
        route.update({"intent": "self_edit_request", "target_area": target, "risk_hint": risk, "requires_tool": True, "tool_hint": "stage2_self_edit", "should_create_plan": risk != "low", "requires_permission": risk != "low"})
        return route
    if "mudou em ti" in t or "mudancas em ti" in t or "o que mudou" in t:
        route.update({"intent": "system_status_request", "target_area": "awareness", "risk_hint": "low", "requires_tool": True, "tool_hint": "self_awareness_answer", "should_execute": True})
        return route
    if any(term in t for term in ("awareness", "nocao", "consciencia", "capacidades", "limitacoes", "limites", "permissoes", "ferramentas", "stage 2", "stage2", "estado")):
        if any(term in t for term in ("tens", "teus", "tuas", "podes", "consegues", "eve", "ti mesma", "mudou")):
            intent = "system_status_request" if "mudou" in t or "estado" in t else "self_awareness_question"
            route.update({"intent": intent, "target_area": "awareness", "risk_hint": "low", "requires_tool": True, "tool_hint": "self_awareness_answer", "should_execute": True})
            return route
    if any(term in t for term in ("registos diarios", "registo diario", "logs diarios", "daily")) and any(term in t for term in ("tecnologia", "mundo", "personalidade", "interesses", "world", "technology", "personality")):
        route.update({"intent": "daily_interest_logs", "target_area": "daily_interest_logs", "risk_hint": "low", "requires_tool": True, "tool_hint": "interest_registers_read", "should_execute": True})
        return route
    if any(term in t for term in ("quem e", "quem é", "o que sabes sobre", "bubu", "sandro", "mia kinsky", "lifepath", "casa principal")):
        route.update({"intent": "memory_question", "target_area": "memory", "risk_hint": "low", "requires_tool": False, "tool_hint": "memory_retrieval", "should_execute": False})
        return route
    if any(term in t for term in ("erro", "falha", "bug", "nao funciona", "não funciona", "crash")):
        route.update({"intent": "troubleshooting_request", "target_area": "runtime", "risk_hint": "medium", "requires_tool": False, "tool_hint": "diagnostics"})
        return route
    route.update({"intent": "normal_chat", "target_area": "conversation", "risk_hint": "low", "confidence": 0.45})
    return route


def _sanitize_route(candidate: dict[str, Any], *, fallback_reason: str) -> dict[str, Any]:
    route = _base_route(str(candidate.get("intent") or "unclear"))
    route.update({key: candidate.get(key, route[key]) for key in route})
    if route["intent"] not in VALID_INTENTS:
        route["intent"] = "unclear"
    try:
        route["confidence"] = max(0.0, min(1.0, float(route.get("confidence", 0.0))))
    except Exception:
        route["confidence"] = 0.0
    if route["risk_hint"] not in VALID_RISKS:
        route["risk_hint"] = "unknown"
    for key in ("requires_tool", "should_create_plan", "should_execute", "requires_permission"):
        route[key] = bool(route.get(key))
    for key in ("target_area", "tool_hint", "reason"):
        route[key] = str(route.get(key) or "")
    if route["risk_hint"] == "critical":
        route["should_execute"] = False
        route["requires_permission"] = True
        route["should_create_plan"] = True
    route["router_mode"] = str(candidate.get("_provider") or candidate.get("router_mode") or fallback_reason)
    if candidate.get("_model"):
        route["model"] = candidate.get("_model")
    return route


def route_message(
    message: str,
    channel: str,
    context: dict[str, Any] | None = None,
    provider: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    prompt = _intent_prompt(message, channel, context)
    provider = provider or ollama_generate_json
    try:
        candidate = provider(prompt)
        route = _sanitize_route(candidate, fallback_reason="llm")
        if route["confidence"] < 0.35:
            fallback = _fallback_route(message, channel, reason="low confidence fallback guardrail")
            fallback["llm_route"] = route
            route = fallback
    except Exception as exc:
        route = _fallback_route(message, channel, reason=f"local LLM unavailable: {type(exc).__name__}")
        route["router_error"] = str(exc)[:500]
    route["channel"] = channel
    return route


def log_router_decision(route: dict[str, Any], message: str, *, route_chosen: str | None = None) -> None:
    ROUTER_DIR.mkdir(parents=True, exist_ok=True)
    path = ROUTER_DIR / f"{datetime.now().astimezone().date().isoformat()}_router_decisions.jsonl"
    row = {
        "timestamp": _now_iso(),
        "channel": route.get("channel", "unknown"),
        "message_excerpt": (message or "")[:180],
        "intent": route.get("intent"),
        "confidence": route.get("confidence"),
        "target_area": route.get("target_area"),
        "risk_hint": route.get("risk_hint"),
        "tool_hint": route.get("tool_hint"),
        "route_chosen": route_chosen or route.get("intent"),
        "reason": route.get("reason"),
        "router_mode": route.get("router_mode"),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")

from __future__ import annotations

from typing import Any

from core.awareness_engine import compact_self_state_text
from core.memory_retrieval import format_memory_context, retrieve_memory_context
from core.session_rollover_context import load_latest_handoff


SIMPLE_MAX_CHARS = 2500
DEFAULT_MAX_CHARS = 4000
COMPLEX_MAX_CHARS = 6000
MAX_CHUNKS = 8
MAX_IDENTITY_CARDS = 3
MAX_HANDOFF_CHARS = 2500
MAX_TOTAL_CONTEXT_CHARS = 6000
MAX_SELF_STATE_CHARS = 1000


def _is_self_awareness_query(message: str) -> bool:
    lowered = (message or "").lower()
    terms = (
        "awareness",
        "estado",
        "servicos",
        "serviços",
        "runtime",
        "sessao",
        "sessão",
        "handoff",
        "rollover",
        "memoria",
        "memória",
        "erros",
        "ficheiros",
        "mudanças",
        "mudancas",
        "pc2",
        "onde estás",
        "onde estas",
        "ligada",
    )
    return any(term in lowered for term in terms)


def _load_self_state_context(message: str) -> str:
    if not _is_self_awareness_query(message):
        return ""
    try:
        return compact_self_state_text(max_chars=MAX_SELF_STATE_CHARS)
    except Exception:
        return ""


def _is_complex_query(message: str) -> bool:
    lowered = (message or "").lower()
    complex_terms = (
        "explica",
        "compara",
        "plano",
        "detalha",
        "historia",
        "arquitetura",
        "funciona",
        "como",
    )
    return len(message or "") > 180 or sum(1 for term in complex_terms if term in lowered) >= 2


def _is_simple_identity_query(message: str) -> bool:
    lowered = (message or "").lower().strip()
    starters = ("quem e", "quem é", "o que e", "o que é", "qual e", "qual é")
    return len(lowered) <= 90 and lowered.startswith(starters)


def _context_limit_for(message: str) -> int:
    if _is_simple_identity_query(message):
        return SIMPLE_MAX_CHARS
    if _is_complex_query(message):
        return COMPLEX_MAX_CHARS
    return DEFAULT_MAX_CHARS


def _public_sources(results: list[Any]) -> list[dict[str, Any]]:
    sources = []
    for item in results[:MAX_CHUNKS]:
        metadata = getattr(item, "metadata", {}) or {}
        sources.append(
            {
                "source_file": getattr(item, "source_file", ""),
                "category": getattr(item, "category", ""),
                "sensitivity": getattr(item, "sensitivity", ""),
                "source_type": metadata.get("source_type"),
                "priority": metadata.get("priority") or metadata.get("importance_hint"),
                "score": getattr(item, "hybrid_score", None),
            }
        )
    return sources


def build_terminal_prompt(user_message: str) -> dict[str, Any]:
    max_chars = _context_limit_for(user_message)
    handoff = load_latest_handoff(MAX_HANDOFF_CHARS)
    self_state = _load_self_state_context(user_message)
    if handoff:
        max_chars = max(1000, min(max_chars, MAX_TOTAL_CONTEXT_CHARS - len(handoff) - 900))
    if self_state:
        max_chars = max(800, min(max_chars, MAX_TOTAL_CONTEXT_CHARS - len(handoff) - len(self_state) - 900))
    retrieval = retrieve_memory_context(user_message, top_k=MAX_CHUNKS, allow_private=True)
    metadata: dict[str, Any] = {
        "memory_enabled": True,
        "max_chars": max_chars,
        "max_chunks": MAX_CHUNKS,
        "max_identity_cards": MAX_IDENTITY_CARDS,
        "handoff_used": bool(handoff),
        "handoff_chars": len(handoff),
        "self_state_used": bool(self_state),
        "self_state_chars": len(self_state),
        "fallback_without_memory": False,
    }
    if not retrieval.get("ok"):
        metadata.update(
            {
                "fallback_without_memory": True,
                "error": retrieval.get("error") or "unknown retrieval error",
                "chunks_used": 0,
                "chars_used": 0,
                "sources": [],
            }
        )
        return {
            "user_message": user_message,
            "memory_context": "",
            "session_handoff": handoff,
            "final_prompt": (
                ("[SESSION HANDOFF]\n" f"{handoff}\n" "[/SESSION HANDOFF]\n\n") if handoff else ""
            )
            + (("[SELF STATE]\n" f"{self_state}\n" "[/SELF STATE]\n\n") if self_state else "")
            + "[USER MESSAGE]\n"
            + f"{user_message}\n"
            + "[/USER MESSAGE]",
            "retrieval_metadata": metadata,
        }

    results = retrieval.get("results", [])[:MAX_CHUNKS]
    memory_context = format_memory_context({"ok": True, "results": results}, max_chars=max_chars)
    identity_count = sum(1 for item in results if (getattr(item, "metadata", {}) or {}).get("source_type") == "identity_card")
    metadata.update(
        {
            "collection": retrieval.get("collection"),
            "chunks_used": len(results),
            "identity_cards_used": min(identity_count, MAX_IDENTITY_CARDS),
            "chars_used": len(memory_context),
            "sources": _public_sources(results),
            "dedupe": retrieval.get("dedupe") or {},
        }
    )
    final_prompt = (
        ("[SESSION HANDOFF]\n" f"{handoff}\n" "[/SESSION HANDOFF]\n\n") if handoff else ""
    ) + (
        ("[SELF STATE]\n" f"{self_state}\n" "[/SELF STATE]\n\n") if self_state else ""
    ) + (
        "[MEMORY CONTEXT]\n"
        f"{memory_context}\n"
        "[/MEMORY CONTEXT]\n\n"
        "[USER MESSAGE]\n"
        f"{user_message}\n"
        "[/USER MESSAGE]"
    )
    return {
        "user_message": user_message,
        "session_handoff": handoff,
        "self_state_context": self_state,
        "memory_context": memory_context,
        "final_prompt": final_prompt,
        "retrieval_metadata": metadata,
    }

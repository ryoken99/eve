from __future__ import annotations

from typing import Any

from core.awareness_engine import compact_self_state_text
from core.terminal_memory_context import (
    COMPLEX_MAX_CHARS,
    DEFAULT_MAX_CHARS,
    MAX_CHUNKS,
    MAX_IDENTITY_CARDS,
    SIMPLE_MAX_CHARS,
    _is_complex_query,
    _is_simple_identity_query,
    _is_self_awareness_query,
)
from core.memory_retrieval import format_memory_context, retrieve_memory_context
from core.session_rollover_context import load_latest_handoff


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


def build_telegram_prompt(user_message: str, chat_metadata: dict | None = None) -> dict[str, Any]:
    max_chars = _context_limit_for(user_message)
    handoff = load_latest_handoff(2500)
    self_state = compact_self_state_text(max_chars=1000) if _is_self_awareness_query(user_message) else ""
    if handoff:
        max_chars = max(1000, min(max_chars, 6000 - len(handoff) - 900))
    if self_state:
        max_chars = max(800, min(max_chars, 6000 - len(handoff) - len(self_state) - 900))
    metadata: dict[str, Any] = {
        "memory_enabled": True,
        "channel": "telegram",
        "max_chars": max_chars,
        "max_chunks": MAX_CHUNKS,
        "max_identity_cards": MAX_IDENTITY_CARDS,
        "handoff_used": bool(handoff),
        "handoff_chars": len(handoff),
        "self_state_used": bool(self_state),
        "self_state_chars": len(self_state),
        "fallback_without_memory": False,
        "chat_metadata": chat_metadata or {},
    }
    retrieval = retrieve_memory_context(user_message, top_k=MAX_CHUNKS, allow_private=True)
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
            "session_handoff": handoff,
            "memory_context": "",
            "final_prompt": (
                ("[SESSION HANDOFF]\n" f"{handoff}\n" "[/SESSION HANDOFF]\n\n") if handoff else ""
            )
            + (("[SELF STATE]\n" f"{self_state}\n" "[/SELF STATE]\n\n") if self_state else "")
            + (
                "[TELEGRAM USER MESSAGE]\n"
                f"{user_message}\n"
                "[/TELEGRAM USER MESSAGE]"
            ),
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
        "[TELEGRAM USER MESSAGE]\n"
        f"{user_message}\n"
        "[/TELEGRAM USER MESSAGE]"
    )
    return {
        "user_message": user_message,
        "session_handoff": handoff,
        "self_state_context": self_state,
        "memory_context": memory_context,
        "final_prompt": final_prompt,
        "retrieval_metadata": metadata,
    }

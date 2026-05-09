from __future__ import annotations

from typing import Any

from memory.semantic_vector.vector_store import add_document, rebuild_memory_index, search_tfidf


class LocalVectorMemoryProvider:
    name = "local_tfidf_vector_provider"

    def sync_turn(self, turn_messages: list[dict[str, Any]]) -> dict[str, Any]:
        indexed = 0
        for message in turn_messages:
            content = str(message.get("content") or "").strip()
            if not content:
                continue
            source = f"turn/{message.get('role', 'unknown')}/{indexed}"
            add_document(source, content, {"role": message.get("role", "unknown")})
            indexed += 1
        return {"provider": self.name, "indexed": indexed}

    def prefetch(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        return search_tfidf(query, limit=limit)


def rebuild_vector_memory() -> dict[str, Any]:
    path = rebuild_memory_index()
    return {"provider": LocalVectorMemoryProvider.name, "index": str(path)}


def vector_prefetch(query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    return LocalVectorMemoryProvider().prefetch(query, limit=limit)


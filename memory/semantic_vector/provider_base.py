from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from memory.semantic_vector import vector_store


@dataclass(frozen=True)
class VectorSearchResult:
    source: str
    content: str
    semantic_score: float
    recency_score: float = 0.0
    importance_score: float = 0.0
    confidence_score: float = 0.0

    @property
    def hybrid_score(self) -> float:
        return round(self.semantic_score * 0.55 + self.recency_score * 0.15 + self.importance_score * 0.2 + self.confidence_score * 0.1, 4)


class VectorProvider(ABC):
    @abstractmethod
    def add_document(self, source: str, content: str, metadata: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError

    @abstractmethod
    def rebuild(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def sync_memory_layers(self) -> Any:
        raise NotImplementedError


class TfidfVectorProvider(VectorProvider):
    def add_document(self, source: str, content: str, metadata: dict[str, Any] | None = None) -> Any:
        return vector_store.add_document(source, content, metadata or {})

    def rebuild(self) -> Any:
        return vector_store.rebuild_memory_index()

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        return vector_store.search_tfidf(query, limit=limit)

    def sync_memory_layers(self) -> Any:
        return self.rebuild()


class LocalEmbeddingProvider(TfidfVectorProvider):
    """Placeholder provider for local neural embeddings; TF-IDF remains fallback."""


def semantic_context_prefetch(query: str, *, limit: int = 5, provider: VectorProvider | None = None) -> list[dict[str, Any]]:
    provider = provider or TfidfVectorProvider()
    now = datetime.now(timezone.utc)
    rows = []
    for row in provider.search(query, limit=limit):
        semantic = float(row.get("score") or row.get("semantic_score") or 0.0)
        content = str(row.get("content") or row.get("text") or row.get("excerpt") or "")
        result = VectorSearchResult(
            source=str(row.get("source") or row.get("path") or "semantic_vector"),
            content=content,
            semantic_score=semantic,
            recency_score=0.2 if now else 0.0,
            importance_score=float(row.get("importance") or 0.5),
            confidence_score=float(row.get("confidence") or 0.6),
        )
        data = row | {"hybrid_score": result.hybrid_score, "semantic_score": semantic}
        rows.append(data)
    return sorted(rows, key=lambda item: item.get("hybrid_score", item.get("score", 0)), reverse=True)

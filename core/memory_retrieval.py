from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings


EVE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = EVE_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from local_embedding_provider import embed_text  # noqa: E402


CHROMA_PATH = EVE_ROOT / "memory" / "vector" / "chroma"
VECTOR_MANIFEST_PATH = EVE_ROOT / "memory" / "vector" / "manifests" / "vector_memory_manifest.json"

COLLECTIONS = {
    "all": "eve_all_memory",
    "private": "eve_private_memory",
    "identity": "eve_identity_memory",
    "entities": "eve_entities_memory",
    "lore": "eve_lore_memory",
    "projects": "eve_projects_memory",
    "agents": "eve_agents_memory",
    "language": "eve_language_memory",
}

STOPWORDS = {
    "a",
    "as",
    "o",
    "os",
    "e",
    "é",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "um",
    "uma",
    "quem",
    "que",
    "qual",
    "quais",
    "como",
    "sobre",
    "sabes",
    "minha",
    "meu",
    "minhas",
    "meus",
    "por",
    "para",
    "com",
    "em",
    "no",
    "na",
}


@dataclass
class RetrievalResult:
    chunk_id: str
    source_file: str
    category: str
    sensitivity: str
    collection: str
    distance: float | None
    score: float | None
    keyword_boost: float
    keyword_hits: int
    hybrid_score: float | None
    content: str
    metadata: dict[str, Any]

    def public_dict(self, *, include_content: bool = False, excerpt_chars: int = 300) -> dict[str, Any]:
        payload = {
            "chunk_id": self.chunk_id,
            "source_file": self.source_file,
            "category": self.category,
            "sensitivity": self.sensitivity,
            "collection": self.collection,
            "distance": self.distance,
            "score": self.score,
            "keyword_boost": self.keyword_boost,
            "keyword_hits": self.keyword_hits,
            "hybrid_score": self.hybrid_score,
            "excerpt": make_excerpt(self.content, max_chars=excerpt_chars),
        }
        if include_content:
            payload["content"] = self.content
        return payload


def load_vector_manifest() -> dict[str, Any]:
    if not VECTOR_MANIFEST_PATH.exists():
        return {"ok": False, "error": "vector manifest not found", "path": str(VECTOR_MANIFEST_PATH)}
    try:
        data = json.loads(VECTOR_MANIFEST_PATH.read_text(encoding="utf-8"))
        data["ok"] = True
        return data
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "path": str(VECTOR_MANIFEST_PATH)}


def get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )


def normalize_collection_name(name: str = "eve_all_memory") -> str:
    if name in COLLECTIONS:
        return COLLECTIONS[name]
    return name or COLLECTIONS["all"]


def get_collection(name: str = "eve_all_memory"):
    return get_chroma_client().get_collection(normalize_collection_name(name))


def choose_collection(category: str | None) -> str:
    if not category:
        return COLLECTIONS["all"]
    normalized = category.lower()
    if normalized in {"private"}:
        return COLLECTIONS["private"]
    if normalized in {"lore", "lore_simulation"}:
        return COLLECTIONS["lore"]
    if normalized == "projects":
        return COLLECTIONS["projects"]
    if normalized == "agents":
        return COLLECTIONS["agents"]
    if normalized == "language":
        return COLLECTIONS["language"]
    return COLLECTIONS["all"]


def is_identity_query(query: str) -> bool:
    lowered = query.lower()
    return any(
        term in lowered
        for term in (
            "quem é",
            "quem e",
            "o que é",
            "o que e",
            "qual é a casa principal",
            "qual e a casa principal",
            "casa principal",
            "o que sabes sobre",
            "identidade",
            "perfil",
            "linguagem criada",
            "master coder",
            "lifepath",
            "project helix",
            "echoes of eternity",
        )
    )


def tokenize(text: str) -> list[str]:
    return [
        token.lower()
        for token in re.findall(r"[\wÀ-ÿ]+", text or "")
        if len(token) > 1 and token.lower() not in STOPWORDS
    ]


def normalize_text(text: str) -> str:
    lowered = (text or "").lower()
    lowered = re.sub(r"^(quem\s+[ée]|o\s+que\s+[ée]|qual\s+[ée]|o\s+que\s+sabes\s+sobre)\s+", "", lowered).strip()
    lowered = re.sub(r"^(a|o|os|as|um|uma)\s+", "", lowered).strip()
    return re.sub(r"\s+", " ", lowered).strip(" ?!.:")


def identity_alias_match(query: str, metadata: dict[str, Any]) -> bool:
    target = normalize_text(query)
    if not target:
        return False
    raw_aliases = metadata.get("aliases_json") or metadata.get("aliases") or "[]"
    try:
        aliases = json.loads(raw_aliases) if isinstance(raw_aliases, str) else raw_aliases
    except Exception:
        aliases = []
    names = [metadata.get("canonical_name", ""), *(aliases or [])]
    for name in names:
        alias = normalize_text(str(name))
        if not alias:
            continue
        if alias == target or alias in target or target in alias:
            if target in {"sandro", "eve", "bubu", "marta", "mia"} and alias != target:
                continue
            return True
    return False


def keyword_signal(query: str, document: str, metadata: dict[str, Any]) -> tuple[float, int]:
    tokens = tokenize(query)
    if not tokens:
        return 0.0, 0
    haystack = " ".join(
        [
            document or "",
            str(metadata.get("source_file", "")),
            str(metadata.get("category", "")),
            str(metadata.get("sensitivity", "")),
        ]
    ).lower()
    hits = sum(1 for token in tokens if token in haystack)
    repeated = sum(min(haystack.count(token), 3) for token in tokens)
    return min(0.18, hits * 0.035 + repeated * 0.01), hits


def identity_intent_boost(query: str, metadata: dict[str, Any]) -> float:
    lowered = query.lower()
    identity_intent = any(term in lowered for term in ("quem é", "quem e", "o que é", "o que e", "o que sabes sobre", "identidade", "perfil"))
    tokens = tokenize(query)
    source = str(metadata.get("source_file", "")).lower()
    category = str(metadata.get("category", "")).lower()
    source_type = str(metadata.get("source_type", "")).lower()
    alias_hit = identity_alias_match(query, metadata)
    if source_type == "identity_card" and alias_hit:
        return 0.85
    if source_type == "identity_card" and identity_intent and str(metadata.get("entity_category", "")).lower() in {"eve_identity", "pc_runtime"} and any(token == "eve" for token in tokens):
        return 0.45
    if not identity_intent:
        return 0.0
    has_named_source = any(token in source for token in tokens)
    if has_named_source and any(term in source for term in ("core", "profile", "identity", "identidade", "entity", "private_core")):
        return 0.25
    if has_named_source and category in {"entities", "sandro_core", "bubu_private", "eve_identity"}:
        return 0.14
    return 0.0


def _source_priority(item: RetrievalResult) -> int:
    source_type = str(item.metadata.get("source_type", "")).lower()
    category = item.category.lower()
    entity_category = str(item.metadata.get("entity_category", "")).lower()
    if source_type == "identity_card" or category == "identity_card":
        return 100
    if "long" in category or entity_category in {"sandro_core", "eve_identity", "pc_runtime"}:
        return 80
    if "medium" in category:
        return 65
    if category in {"projects", "agents", "language", "technical"}:
        return 55
    if category in {"lore", "lore_simulation"}:
        return 45
    if category in {"transcripts"}:
        return 20
    return 40


def _dedupe_results(rows: list[RetrievalResult], *, max_identity_cards: int = 3) -> tuple[list[RetrievalResult], dict[str, Any]]:
    selected: list[RetrievalResult] = []
    seen_hashes: set[str] = set()
    seen_source_sections: set[str] = set()
    identity_sources: set[str] = set()
    removed = {"same_hash": 0, "same_source_section": 0, "identity_limit": 0}
    for row in rows:
        content_hash = str(row.metadata.get("content_hash") or "").strip()
        if content_hash and content_hash in seen_hashes:
            removed["same_hash"] += 1
            continue
        source_type = str(row.metadata.get("source_type", "")).lower()
        is_identity = source_type == "identity_card" or row.category == "identity_card"
        section_key = f"{row.source_file}:{row.metadata.get('canonical_name') or ''}:{row.metadata.get('chunk_index') or ''}"
        if section_key in seen_source_sections:
            removed["same_source_section"] += 1
            continue
        if is_identity:
            if row.source_file in identity_sources:
                removed["same_source_section"] += 1
                continue
            if len(identity_sources) >= max_identity_cards:
                removed["identity_limit"] += 1
                continue
            identity_sources.add(row.source_file)
        if content_hash:
            seen_hashes.add(content_hash)
        seen_source_sections.add(section_key)
        selected.append(row)
    return selected, {"removed": removed, "identity_cards": len(identity_sources)}


def content_quality_penalty(document: str, keyword_hits: int) -> float:
    stripped = re.sub(r"\s+", " ", document or "").strip()
    length = len(stripped)
    penalty = 0.0
    if length < 80:
        penalty += 0.4
    elif length < 160:
        penalty += 0.16
    if keyword_hits == 0:
        penalty += 0.22
    return penalty


def metadata_allowed(metadata: dict[str, Any], category: str | None, sensitivity: str | None, allow_private: bool) -> bool:
    if category and metadata.get("category") != category:
        if not (category == "lore" and metadata.get("category") == "lore_simulation"):
            return False
    if sensitivity and metadata.get("sensitivity") != sensitivity:
        return False
    if not allow_private and "private" in str(metadata.get("sensitivity", "")).lower():
        return False
    return True


def retrieve_memory_context(
    query: str,
    top_k: int = 8,
    category: str | None = None,
    sensitivity: str | None = None,
    allow_private: bool = True,
) -> dict[str, Any]:
    if not query or not query.strip():
        return {"ok": False, "error": "empty query", "results": []}
    try:
        manifest = load_vector_manifest()
        collection_name = COLLECTIONS["identity"] if category is None and is_identity_query(query) else choose_collection(category)
        collection = get_collection(collection_name)
        query_embedding = embed_text(query)
        collection_count = collection.count()
        candidate_count = min(max(top_k * 8, 250), collection_count, 1000)
        raw = collection.query(
            query_embeddings=[query_embedding],
            n_results=candidate_count,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "results": [],
            "manifest": load_vector_manifest(),
        }

    rows: list[RetrievalResult] = []
    ids = raw.get("ids", [[]])[0]
    documents = raw.get("documents", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]
    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        metadata = metadata or {}
        if not metadata_allowed(metadata, category, sensitivity, allow_private):
            continue
        semantic_score = None if distance is None else 1 - float(distance)
        boost, keyword_hits = keyword_signal(query, document or "", metadata)
        boost += identity_intent_boost(query, metadata)
        penalty = content_quality_penalty(document or "", keyword_hits) if tokenize(query) else 0.0
        hybrid = None if semantic_score is None else semantic_score + boost - penalty
        rows.append(
            RetrievalResult(
                chunk_id=str(chunk_id),
                source_file=str(metadata.get("source_file", "")),
                category=str(metadata.get("category", "")),
                sensitivity=str(metadata.get("sensitivity", "")),
                collection=collection_name,
                distance=None if distance is None else float(distance),
                score=semantic_score,
                keyword_boost=boost,
                keyword_hits=keyword_hits,
                hybrid_score=hybrid,
                content=document or "",
                metadata=metadata,
            )
        )
    rows.sort(key=lambda item: ((_source_priority(item) / 1000) + (item.hybrid_score or 0)), reverse=True)
    lowered_query = query.lower()
    if is_identity_query(query) and "casa principal" not in lowered_query:
        direct_identity_rows = [
            row
            for row in rows
            if (str(row.metadata.get("source_type", "")).lower() == "identity_card" or row.category == "identity_card")
            and identity_alias_match(query, row.metadata)
        ]
        if direct_identity_rows:
            direct_ids = {row.chunk_id for row in direct_identity_rows}
            rows = direct_identity_rows + [row for row in rows if row.chunk_id not in direct_ids and row.category != "identity_card"]
    deduped, dedupe_info = _dedupe_results(rows, max_identity_cards=3)
    selected = deduped[: min(top_k, 8)]
    return {
        "ok": True,
        "query": query,
        "top_k": top_k,
        "category": category,
        "sensitivity": sensitivity,
        "allow_private": allow_private,
        "collection": collection_name,
        "manifest": {
            "ok": manifest.get("ok"),
            "embedding_model": manifest.get("embedding_model"),
            "last_build": manifest.get("built_at"),
            "chunks_indexed": manifest.get("chunks_indexed"),
        },
        "dedupe": dedupe_info,
        "results": selected,
    }


def make_excerpt(text: str, max_chars: int = 300) -> str:
    flat = re.sub(r"\s+", " ", text or "").strip()
    if len(flat) <= max_chars:
        return flat
    return flat[:max_chars].rstrip() + "..."


def format_memory_context(results: dict[str, Any] | list[RetrievalResult], max_chars: int = 4000) -> str:
    if isinstance(results, dict):
        if not results.get("ok"):
            return f"[memory retrieval unavailable: {results.get('error', 'unknown error')}]"
        items = results.get("results", [])
    else:
        items = results

    lines = []
    used = 0
    for index, item in enumerate(items, start=1):
        if isinstance(item, RetrievalResult):
            header = (
                f"[{index}] source={item.source_file} category={item.category} "
                f"sensitivity={item.sensitivity} score={item.hybrid_score:.3f}"
            )
            source_type = str(item.metadata.get("source_type") or "").strip()
            priority = str(item.metadata.get("priority") or item.metadata.get("importance_hint") or "").strip()
            extra = []
            if source_type:
                extra.append(f"type={source_type}")
            if priority:
                extra.append(f"priority={priority}")
            suffix = " " + " ".join(extra) if extra else ""
            header = header + suffix
            body = make_excerpt(item.content, max_chars=650)
        else:
            header = f"[{index}] source={item.get('source_file')} category={item.get('category')} sensitivity={item.get('sensitivity')}"
            body = str(item.get("excerpt") or item.get("content") or "")
        block = f"{header}\n{body}\n"
        if used + len(block) > max_chars:
            remaining = max_chars - used
            if remaining > 120:
                lines.append(block[:remaining].rstrip() + "\n[context truncated]")
            break
        lines.append(block)
        used += len(block)
    return "\n".join(lines).strip() or "[no relevant memory context found]"


def build_prompt_context(user_message: str, top_k: int = 8) -> str:
    retrieval = retrieve_memory_context(user_message, top_k=top_k, allow_private=True)
    context = format_memory_context(retrieval, max_chars=4000)
    return f"[MEMORY CONTEXT]\n{context}\n[/MEMORY CONTEXT]\n\n[USER MESSAGE]\n{user_message}\n[/USER MESSAGE]"

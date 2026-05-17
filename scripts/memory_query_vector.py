from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import chromadb
from chromadb.config import Settings

from local_embedding_provider import embed_text


EVE_ROOT = Path(__file__).resolve().parents[1]
CHROMA_PATH = EVE_ROOT / "memory" / "vector" / "chroma"

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


def client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )


def excerpt(content: str, radius: int = 260) -> str:
    flat = re.sub(r"\s+", " ", content or "").strip()
    if len(flat) <= radius:
        return flat
    return flat[:radius].rstrip() + "..."


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


def identity_alias_match(query: str, metadata: dict) -> bool:
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


def keyword_signal(query: str, document: str, metadata: dict) -> tuple[float, int]:
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


def identity_intent_boost(query: str, metadata: dict) -> float:
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


def choose_collection(category: str | None) -> str:
    if not category:
        return COLLECTIONS["all"]
    normalized = category.lower()
    if normalized in ("lore", "lore_simulation"):
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
            "identidade",
            "perfil",
            "linguagem criada",
            "master coder",
            "lifepath",
            "project helix",
            "echoes of eternity",
        )
    )


def metadata_match(metadata: dict, category: str | None, sensitivity: str | None) -> bool:
    if category and metadata.get("category") != category:
        if not (category == "lore" and metadata.get("category") == "lore_simulation"):
            return False
    if sensitivity and metadata.get("sensitivity") != sensitivity:
        return False
    return True


def query_vector(query: str, top_k: int = 5, category: str | None = None, sensitivity: str | None = None) -> dict:
    query_embedding = embed_text(query)
    collection_name = COLLECTIONS["identity"] if category is None and is_identity_query(query) else choose_collection(category)
    col = client().get_collection(collection_name)
    raw_n = max(top_k * 4, top_k)
    try:
        collection_count = col.count()
    except Exception:
        collection_count = raw_n
    candidate_count = min(max(raw_n, 250), collection_count, 1000)
    result = col.query(
        query_embeddings=[query_embedding],
        n_results=candidate_count,
        include=["documents", "metadatas", "distances"],
    )
    rows = []
    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        if not metadata_match(metadata or {}, category, sensitivity):
            continue
        semantic_score = None if distance is None else 1 - float(distance)
        boost, keyword_hits = keyword_signal(query, document, metadata or {})
        boost += identity_intent_boost(query, metadata or {})
        no_hit_penalty = content_quality_penalty(document, keyword_hits) if tokenize(query) else 0.0
        rows.append(
            {
                "distance": distance,
                "score": semantic_score,
                "keyword_boost": boost,
                "keyword_hits": keyword_hits,
                "hybrid_score": None if semantic_score is None else semantic_score + boost - no_hit_penalty,
                "chunk_id": chunk_id,
                "source_file": metadata.get("source_file") if metadata else None,
                "category": metadata.get("category") if metadata else None,
                "sensitivity": metadata.get("sensitivity") if metadata else None,
                "collection": collection_name,
                "excerpt": excerpt(document),
            }
        )
    rows.sort(key=lambda item: item.get("hybrid_score") or 0, reverse=True)
    rows = rows[:top_k]
    return {
        "query": query,
        "collection": collection_name,
        "category_filter": category,
        "sensitivity_filter": sensitivity,
        "top_k": top_k,
        "results": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Semantic query over Eve local Chroma vector memory.")
    parser.add_argument("query")
    parser.add_argument("--category")
    parser.add_argument("--sensitivity")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    payload = query_vector(args.query, top_k=args.top_k, category=args.category, sensitivity=args.sensitivity)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

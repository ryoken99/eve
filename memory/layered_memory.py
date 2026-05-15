from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from core.paths import LOGS_DIR, MEMORY_DIR, ensure_project_dirs
from memory.semantic_vector.vector_store import add_document


LAYER_RULES: dict[str, dict[str, Any]] = {
    "short_term": {
        "description": "Contexto imediato usado para a tarefa atual.",
        "keywords": ("agora", "tarefa atual", "ficheiro em edicao", "janela ativa", "erro recente", "hoje"),
        "file": "current_session.md",
    },
    "medium_term": {
        "description": "Projetos, decisoes recentes e padroes que ainda podem mudar.",
        "keywords": ("projeto", "decisao recente", "padrao", "skill em teste", "esta semana", "iterar"),
        "file": "layered_observations.md",
    },
    "long_term": {
        "description": "Factos estaveis, preferencias persistentes, regras centrais e correcoes importantes.",
        "keywords": ("sempre", "preferencia estavel", "regra", "missao", "constituicao", "sandro e", "correcao importante"),
        "file": "stable_memories.md",
    },
    "archive_only": {
        "description": "Fica no diario/log bruto, sem entrar na memoria viva.",
        "keywords": ("duplicado", "ruido", "temporario expirado", "sem valor futuro"),
        "file": "archive_only.md",
    },
}


class MemoryDecision(str, Enum):
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"
    ARCHIVE = "archive"
    REJECT = "reject"


@dataclass(frozen=True)
class MemoryItem:
    id: str
    content: str
    layer: str = "medium_term"
    source: str = "unknown"
    confidence: float = 0.6
    stability: float = 0.4
    importance: float = 0.5
    created_at: str = ""
    updated_at: str = ""
    evidence_count: int = 1
    tags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_memory_item(content: str, **kwargs: Any) -> MemoryItem:
    now = _now_iso()
    return MemoryItem(id=f"mem_{uuid.uuid4().hex[:12]}", content=content, created_at=now, updated_at=now, **kwargs)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def classify_memory_item(text: str, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = metadata or {}
    lowered = text.lower()
    if metadata.get("stable") is True:
        layer = "long_term"
        reason = "metadata stable=true"
    elif metadata.get("ttl") or metadata.get("temporary"):
        layer = "short_term"
        reason = "metadata marks temporary/current context"
    else:
        scores = {
            layer: sum(1 for keyword in data["keywords"] if keyword in lowered)
            for layer, data in LAYER_RULES.items()
        }
        layer = max(scores, key=lambda item: (scores[item], item == "medium_term"))
        if scores[layer] == 0:
            layer = "medium_term"
            reason = "default: useful but not stable enough for long-term"
        else:
            reason = f"matched {scores[layer]} rule keyword(s)"
    return {
        "layer": layer,
        "target_file": LAYER_RULES[layer]["file"],
        "description": LAYER_RULES[layer]["description"],
        "reason": reason,
        "metadata": metadata,
    }


def route_memory_item(text: str, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_project_dirs()
    decision = classify_memory_item(text, metadata=metadata)
    target = MEMORY_DIR / decision["layer"] / decision["target_file"]
    target.parent.mkdir(parents=True, exist_ok=True)
    line = f"- {_now_iso()}: {text.strip()} [reason: {decision['reason']}]\n"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(line)
    log_path = LOGS_DIR / "autonomy" / "memory_layering.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {"timestamp": _now_iso(), "text": text, "decision": decision, "path": str(target)}
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    index_path = add_document(f"layered_memory/{decision['layer']}/{decision['target_file']}", text, {"path": str(target), "layer": decision["layer"]})
    return {"decision": decision, "path": str(target), "log_path": str(log_path), "vector_index": str(index_path)}


def promote_memory_item(item: MemoryItem | dict[str, Any]) -> dict[str, Any]:
    data = item.as_dict() if isinstance(item, MemoryItem) else dict(item)
    evidence = int(data.get("evidence_count") or 1)
    importance = float(data.get("importance") or 0.5)
    confidence = float(data.get("confidence") or 0.6)
    if evidence >= 3 and confidence >= 0.75 and importance >= 0.7:
        data["layer"] = MemoryDecision.LONG_TERM.value
    elif evidence >= 2 or importance >= 0.55:
        data["layer"] = MemoryDecision.MEDIUM_TERM.value
    else:
        data["layer"] = MemoryDecision.SHORT_TERM.value
    data["updated_at"] = _now_iso()
    return data


def deduplicate_memory_item(item: MemoryItem | dict[str, Any], existing: list[dict[str, Any]]) -> dict[str, Any]:
    data = item.as_dict() if isinstance(item, MemoryItem) else dict(item)
    normalized = " ".join(str(data.get("content", "")).lower().split())
    for row in existing:
        if " ".join(str(row.get("content", "")).lower().split()) == normalized:
            merged = dict(row)
            merged["evidence_count"] = int(merged.get("evidence_count") or 1) + int(data.get("evidence_count") or 1)
            merged["updated_at"] = _now_iso()
            return merged
    return data


def decay_memory_item(item: MemoryItem | dict[str, Any], *, amount: float = 0.05) -> dict[str, Any]:
    data = item.as_dict() if isinstance(item, MemoryItem) else dict(item)
    data["importance"] = max(0.0, round(float(data.get("importance") or 0.5) - amount, 3))
    data["confidence"] = max(0.0, round(float(data.get("confidence") or 0.6) - amount / 2, 3))
    data["updated_at"] = _now_iso()
    return data

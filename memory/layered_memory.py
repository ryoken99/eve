from __future__ import annotations

import json
from datetime import datetime, timezone
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

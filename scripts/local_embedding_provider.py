from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


EVE_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = EVE_ROOT / "logs" / "vector_memory"
LOG_PATH = LOG_DIR / "local_embedding_provider.log"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_EMBEDDINGS_URL = f"{OLLAMA_BASE_URL}/api/embeddings"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"
EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_TIMEOUT_SECONDS = 60


class LocalEmbeddingError(RuntimeError):
    pass


def _log(event: str, **fields: Any) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "event": event,
        **fields,
    }
    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def check_ollama_embedding_model() -> dict:
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        _log("ollama_unavailable", error=type(exc).__name__)
        return {
            "ok": False,
            "base_url": OLLAMA_BASE_URL,
            "model": EMBEDDING_MODEL,
            "error": f"Ollama is not reachable on {OLLAMA_BASE_URL}: {type(exc).__name__}",
        }

    data = response.json()
    models = [item.get("name", "") for item in data.get("models", [])]
    present = any(name == EMBEDDING_MODEL or name.startswith(f"{EMBEDDING_MODEL}:") for name in models)
    result = {
        "ok": present,
        "base_url": OLLAMA_BASE_URL,
        "model": EMBEDDING_MODEL,
        "models": models,
        "error": None if present else f"Model {EMBEDDING_MODEL} is not installed in Ollama.",
    }
    _log("ollama_model_check", model=EMBEDDING_MODEL, present=present, model_count=len(models))
    return result


def embed_text(text: str) -> list[float]:
    if not text or not text.strip():
        raise LocalEmbeddingError("Cannot embed empty text.")
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text,
    }
    started = time.perf_counter()
    try:
        response = requests.post(OLLAMA_EMBEDDINGS_URL, json=payload, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        _log("embedding_request_failed", error=type(exc).__name__, text_length=len(text))
        raise LocalEmbeddingError(f"Local Ollama embedding failed: {type(exc).__name__}") from exc

    data = response.json()
    embedding = data.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        _log("embedding_response_invalid", text_length=len(text))
        raise LocalEmbeddingError("Ollama returned no embedding.")
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    _log("embedding_created", model=EMBEDDING_MODEL, text_length=len(text), dimensions=len(embedding), elapsed_ms=elapsed_ms)
    return [float(value) for value in embedding]


def embed_batch(texts: list[str]) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for text in texts:
        embeddings.append(embed_text(text))
    return embeddings


if __name__ == "__main__":
    print(json.dumps(check_ollama_embedding_model(), ensure_ascii=False, indent=2))

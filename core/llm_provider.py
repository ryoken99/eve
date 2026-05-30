from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_INTENT_MODEL = os.environ.get("EVE_INTENT_ROUTER_MODEL", "llama3.2:latest")


def ollama_generate_json(
    prompt: str,
    *,
    model: str | None = None,
    base_url: str | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Call a local Ollama model and parse a JSON object response.

    This provider is local-only by design. It never calls external APIs.
    """

    selected_model = model or DEFAULT_INTENT_MODEL
    url = (base_url or os.environ.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }
    request = urllib.request.Request(
        f"{url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Ollama intent model HTTP {exc.code}: {body}") from exc
    except Exception as exc:
        raise RuntimeError(f"Ollama intent model unavailable: {type(exc).__name__}: {exc}") from exc

    text = str(raw.get("response") or "").strip()
    if not text:
        raise RuntimeError("Ollama intent model returned an empty response")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Ollama intent model returned invalid JSON: {text[:500]}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("Ollama intent model returned JSON that is not an object")
    parsed["_provider"] = "ollama"
    parsed["_model"] = selected_model
    return parsed

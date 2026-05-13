from __future__ import annotations

import re
from pathlib import Path


def chunk_text(text: str, *, max_tokens: int = 500, overlap: int = 80) -> list[str]:
    tokens = re.findall(r"\S+", text)
    if not tokens:
        return []
    chunks = []
    step = max(1, max_tokens - overlap)
    for start in range(0, len(tokens), step):
        chunk = tokens[start : start + max_tokens]
        if chunk:
            chunks.append(" ".join(chunk))
        if start + max_tokens >= len(tokens):
            break
    return chunks


def chunk_document(path: str | Path, *, max_tokens: int = 500, overlap: int = 80) -> list[dict]:
    target = Path(path)
    text = target.read_text(encoding="utf-8", errors="replace")
    return [{"chunk_id": f"{target.name}:{index}", "source": str(target), "content": content} for index, content in enumerate(chunk_text(text, max_tokens=max_tokens, overlap=overlap))]

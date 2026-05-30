from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


EVE_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = EVE_ROOT / "memory" / "_processed" / "chunks" / "imported_memory_chunks.jsonl"


def load_chunks(path: Path = CHUNKS_PATH) -> list[dict]:
    if not path.exists():
        return []
    chunks = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            chunks.append(json.loads(line))
    return chunks


def tokenize(query: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[\wÀ-ÿ]+", query) if len(token) > 1]


def score_chunk(chunk: dict, tokens: list[str]) -> int:
    content = f"{chunk.get('source_file', '')}\n{chunk.get('category', '')}\n{chunk.get('content', '')}".lower()
    return sum(content.count(token) for token in tokens)


def excerpt(content: str, tokens: list[str], radius: int = 180) -> str:
    flat = re.sub(r"\s+", " ", content).strip()
    if not flat:
        return ""
    lower = flat.lower()
    positions = [lower.find(token) for token in tokens if lower.find(token) >= 0]
    if not positions:
        return flat[: radius * 2]
    pos = min(positions)
    start = max(0, pos - radius)
    end = min(len(flat), pos + radius)
    prefix = "..." if start else ""
    suffix = "..." if end < len(flat) else ""
    return f"{prefix}{flat[start:end]}{suffix}"


def search(query: str, limit: int = 8) -> list[dict]:
    tokens = tokenize(query)
    if not tokens:
        return []
    scored = []
    for chunk in load_chunks():
        score = score_chunk(chunk, tokens)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda item: (-item[0], item[1].get("source_file", "")))
    results = []
    for score, chunk in scored[:limit]:
        results.append(
            {
                "score": score,
                "chunk_id": chunk.get("chunk_id"),
                "source_file": chunk.get("source_file"),
                "category": chunk.get("category"),
                "sensitivity": chunk.get("sensitivity"),
                "excerpt": excerpt(chunk.get("content", ""), tokens),
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Plain text search over imported Eve memory chunks.")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    payload = {
        "query": args.query,
        "chunks_path": str(CHUNKS_PATH),
        "results": search(args.query, limit=args.limit),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

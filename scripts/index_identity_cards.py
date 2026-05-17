from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


EVE_ROOT = Path(__file__).resolve().parents[1]
CARDS_DIR = EVE_ROOT / "memory" / "long_term" / "_identity_cards"
MANIFEST_PATH = EVE_ROOT / "memory" / "_system" / "identity_cards_manifest.json"
OUTPUT_PATH = EVE_ROOT / "memory" / "_processed" / "chunks" / "identity_card_chunks.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()


def stable_chunk_id(card_name: str, index: int, content: str) -> str:
    return "identity_" + hashlib.sha256(f"{card_name}:{index}:{content_hash(content)}".encode("utf-8")).hexdigest()[:24]


def load_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def read_card(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def split_card(text: str) -> list[str]:
    sections = re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)
    chunks: list[str] = []
    header = ""
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if section.startswith("# "):
            header = section
            continue
        chunks.append(f"{header}\n\n{section}".strip() if header else section)
    if not chunks and text:
        chunks.append(text)
    return chunks


def build_chunks() -> list[dict]:
    imported_at = utc_now()
    chunks: list[dict] = []
    for entry in load_manifest():
        path = Path(entry["path"])
        if not path.exists():
            continue
        text = read_card(path)
        aliases = entry.get("aliases") or []
        for index, content in enumerate(split_card(text)):
            chunks.append(
                {
                    "chunk_id": stable_chunk_id(entry["card_name"], index, content),
                    "source_file": entry["card_name"],
                    "source_path": str(path),
                    "source_name": path.stem,
                    "source_type": "identity_card",
                    "version": "identity_card_v1",
                    "category": "identity_card",
                    "entity_category": entry.get("category", ""),
                    "sensitivity": entry.get("sensitivity", ""),
                    "importance_hint": 5,
                    "priority": entry.get("priority", 5),
                    "chunk_index": index,
                    "canonical_name": entry.get("canonical_name", ""),
                    "aliases": aliases,
                    "aliases_json": json.dumps(aliases, ensure_ascii=False),
                    "content": content,
                    "content_hash": content_hash(content),
                    "imported_at": imported_at,
                }
            )
    return chunks


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    chunks = build_chunks()
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "ok": True,
        "cards_dir": str(CARDS_DIR),
        "manifest": str(MANIFEST_PATH),
        "output": str(OUTPUT_PATH),
        "chunks_written": len(chunks),
        "cards_indexed": len({chunk["source_file"] for chunk in chunks}),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

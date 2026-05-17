from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


EVE_ROOT = Path(__file__).resolve().parents[1]
MEMORY_ROOT = EVE_ROOT / "memory"
IMPORT_ROOT = MEMORY_ROOT / "_inbox" / "imports" / "memory_v1_to_v7"
CHUNKS_PATH = MEMORY_ROOT / "_processed" / "chunks" / "imported_memory_chunks.jsonl"
MANIFEST_PATH = MEMORY_ROOT / "_system" / "imported_memory_manifest.json"

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".log",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()


def stable_chunk_id(source_file: str, index: int, content: str) -> str:
    payload = f"{source_file}:{index}:{content_hash(content)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def detect_version(path: Path) -> str:
    name = path.name.lower()
    patterns = [
        (r"(?:^|[_\-\s])v([1-7])(?:[_\-\.\s]|$)", "V{}"),
        (r"memoria_eve_base_v1|memory_base_v1|base_v1", "V1"),
        (r"fases_11_19|phase11|continuation_11_13", "V2"),
        (r"meu_mundo|master_timeline_v3", "V3"),
        (r"categorias_mistas", "V4"),
        (r"mastercoder|master_coder", "V5"),
        (r"mastermind_language", "V6"),
        (r"internal_memory_v7|internal_chatgpt|_v7", "V7"),
    ]
    for pattern, value in patterns:
        match = re.search(pattern, name)
        if match:
            return value.format(match.group(1)) if "{}" in value else value
    return "unknown"


def manifest_category(path: Path) -> str:
    text = path.name.lower()
    if "memoria_eve_base" in text or "memory_base" in text or "core_memory" in text:
        return "base_memory"
    if "meu_mundo" in text or "lifepath" in text or "lore" in text or "kingdom" in text:
        return "simulation_lore"
    if "categorias_mistas" in text or "mixed" in text or "changelog" in text:
        return "mixed_memory"
    if "mastercoder" in text or "agent_" in text or "architecture" in text:
        return "agent_architecture"
    if "language" in text or "protoc" in text or "conlang" in text:
        return "language_and_protocols"
    if "internal" in text or "chatgpt" in text:
        return "internal_chatgpt_memory"
    return "unknown_import"


def infer_category(path: Path, text: str) -> str:
    filename = path.name.lower()
    path_text = str(path).lower()
    path_checks = [
        ("bubu_private", ["bubu", "marta"]),
        ("language", ["language", "linguagem", "conlang", "translator", "tradutor"]),
        ("entities", ["entities", "entity", "mia_kinsky", "ayla", "emma", "naomi", "inari"]),
        ("lore_simulation", ["lifepath", "lore", "kingdom", "reinos", "magic", "kaelen", "helix", "alvorada"]),
        ("projects", ["project", "creative_projects", "game", "rpg", "pygame", "prototype", "echoes_of_eternity"]),
        ("agents", ["agent_", "mastermind", "mastercoder", "master_coder", "protocol"]),
        ("pc_runtime", ["pc_runtime", "pc_hardware", "local_eve", "runtime_context", "telegram", "remote_access"]),
        ("sandro_core", ["sandro_core", "sandro_profile", "sandro_social", "sandro_rap"]),
        ("eve_identity", ["eve_", "persona", "identity", "values", "operating_style"]),
        ("personality", ["preferences", "communication_style", "taste"]),
        ("technical", ["python", "code", "tool", "terminal", "github"]),
    ]
    for category, needles in path_checks:
        if any(needle in filename or needle in path_text for needle in needles):
            return category

    haystack = f"{filename}\n{text[:2000]}".lower()
    checks = [
        ("bubu_private", ["bubu", "marta"]),
        ("pc_runtime", ["pc2", "pc 2", "e:\\eve", "runtime", "web ui", "telegram bridge"]),
        ("eve_identity", ["eve", "identity", "persona", "operating style", "pc roles"]),
        ("sandro_core", ["sandro", "core identity", "profile", "cv"]),
        ("language", ["language", "linguagem", "conlang", "protocol"]),
        ("agents", ["agent", "mastermind", "mastercoder", "autonomous"]),
        ("technical", ["python", "code", "tool", "terminal", "github", "remote access"]),
        ("projects", ["project", "rpg", "game", "prototype", "echoes of eternity"]),
        ("lore_simulation", ["lifepath", "lore", "kingdom", "magic", "simulation", "kaelen"]),
        ("entities", ["entities", "entity", "mia kinsky", "ayla", "emma", "naomi"]),
        ("personality", ["preference", "taste", "style", "values"]),
        ("knowledge_technology", ["ai", "openai", "model", "technology"]),
        ("knowledge_world", ["world", "culture", "markets", "ecosystem"]),
        ("transcripts", ["conversation", "chat", "transcript"]),
    ]
    for category, needles in checks:
        if any(needle in haystack for needle in needles):
            return category
    return "unknown"


def infer_sensitivity(path: Path, text: str) -> str:
    filename = path.name.lower()
    haystack = f"{filename}\n{text[:2500]}".lower()
    if any(term in filename for term in ["bubu_health", "health", "body_goals", "training_plan"]):
        return "health_private"
    if any(term in filename for term in ["bubu", "marta"]) or any(term in haystack for term in ["relationship", "relaç", "private core"]):
        return "relationship_private"
    if any(term in haystack for term in ["token", "secret", "password", "senha", "telegram", "remote access"]):
        return "technical_private"
    if any(term in filename for term in ["lifepath", "lore", "kingdom", "reinos", "magic", "helix", "alvorada"]):
        return "lore"
    if any(term in filename for term in ["language", "linguagem", "conlang", "translator", "tradutor"]):
        return "private"
    if any(term in haystack for term in ["sandro", "profile", "cv", "family", "business", "social"]):
        return "sensitive_private"
    if any(term in haystack for term in ["lifepath", "lore", "simulation", "worldbuilding", "magic"]):
        return "lore"
    if any(term in haystack for term in ["private", "privado", "memory", "memória", "memoria"]):
        return "private"
    return "unknown"


def infer_importance_hint(path: Path, text: str) -> int:
    haystack = f"{path.name}\n{text[:2500]}".lower()
    if any(term in haystack for term in ["pc2", "pc 2", "casa principal", "permanent", "regra permanente", "core identity"]):
        return 5
    if any(term in haystack for term in ["bubu", "health", "saude", "saúde", "project", "active", "runtime"]):
        return 4
    if any(term in haystack for term in ["error", "lesson", "task", "todo", "lore", "lifepath"]):
        return 3
    if any(term in haystack for term in ["amanhã", "tomorrow", "testar", "temporary"]):
        return 2
    return 1


def split_text_into_chunks(text: str, source_file: Path, max_chars: int = 2600) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    paragraphs = re.split(r"\n\s*\n", normalized)
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            for start in range(0, len(paragraph), max_chars):
                part = paragraph[start : start + max_chars].strip()
                if part:
                    chunks.append(part)
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) > max_chars and current:
            chunks.append(current.strip())
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current.strip())
    return chunks


def split_markdown_into_chunks(text: str, source_file: Path, max_chars: int = 2600) -> list[str]:
    sections = re.split(r"(?=^#{1,6}\s+)", text, flags=re.MULTILINE)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        chunks.extend(split_text_into_chunks(section, source_file, max_chars=max_chars))
    return chunks


def scan_memory_sources(import_root: Path = IMPORT_ROOT) -> list[Path]:
    if not import_root.exists():
        return []
    return sorted(
        path
        for path in import_root.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS
    )


def build_manifest(files: Iterable[Path], imported_at: str) -> list[dict]:
    entries = []
    for path in files:
        try:
            stat = path.stat()
        except OSError:
            continue
        entries.append(
            {
                "source_name": path.name,
                "source_path": str(path),
                "version": detect_version(path),
                "category": manifest_category(path),
                "private_level": "local_private_source",
                "imported_at": imported_at,
                "file_count": 1,
                "total_size_bytes": stat.st_size,
                "status": "detected",
                "notes": "Source detected only; raw source remains in inbox and is not promoted.",
            }
        )
    return entries


def build_chunks(files: Iterable[Path], imported_at: str) -> list[dict]:
    chunks: list[dict] = []
    for path in files:
        text = read_text_file(path)
        split_fn = split_markdown_into_chunks if path.suffix.lower() == ".md" else split_text_into_chunks
        parts = split_fn(text, path)
        for index, content in enumerate(parts):
            chunks.append(
                {
                    "chunk_id": stable_chunk_id(str(path), index, content),
                    "source_file": path.name,
                    "source_path": str(path),
                    "source_name": path.stem,
                    "version": detect_version(path),
                    "category": infer_category(path, text),
                    "sensitivity": infer_sensitivity(path, text),
                    "importance_hint": infer_importance_hint(path, text),
                    "chunk_index": index,
                    "content": content,
                    "content_hash": content_hash(content),
                    "imported_at": imported_at,
                }
            )
    return chunks


def write_chunks_jsonl(chunks: Iterable[dict], output_path: Path = CHUNKS_PATH) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def write_manifest(entries: list[dict], output_path: Path = MANIFEST_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare local Eve memory V1-V7 chunks without promotion or embeddings.")
    parser.add_argument("--input", type=Path, default=IMPORT_ROOT)
    parser.add_argument("--chunks-output", type=Path, default=CHUNKS_PATH)
    parser.add_argument("--manifest-output", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()

    imported_at = utc_now()
    files = scan_memory_sources(args.input)
    manifest = build_manifest(files, imported_at)
    chunks = build_chunks(files, imported_at)
    write_manifest(manifest, args.manifest_output)
    chunk_count = write_chunks_jsonl(chunks, args.chunks_output)
    result = {
        "ok": True,
        "input": str(args.input),
        "manifest": str(args.manifest_output),
        "chunks_output": str(args.chunks_output),
        "files_detected": len(files),
        "chunks_written": chunk_count,
        "categories": sorted({chunk["category"] for chunk in chunks}),
        "sensitivities": sorted({chunk["sensitivity"] for chunk in chunks}),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

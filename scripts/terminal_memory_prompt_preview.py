from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from core.terminal_memory_context import build_terminal_prompt


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview memory context injection for a future Eve terminal prompt.")
    parser.add_argument("message")
    args = parser.parse_args()
    payload = build_terminal_prompt(args.message)
    metadata = payload["retrieval_metadata"]
    print(f"Pergunta: {args.message}")
    print(f"Chunks usados: {metadata.get('chunks_used', 0)}")
    print(f"Identity cards usados: {metadata.get('identity_cards_used', 0)}")
    print(f"Caracteres injectados: {metadata.get('chars_used', 0)} / {metadata.get('max_chars')}")
    print("Source files:")
    for source in metadata.get("sources", []):
        print(
            f"- {source.get('source_file')} | category={source.get('category')} "
            f"sensitivity={source.get('sensitivity')} type={source.get('source_type')}"
        )
    if metadata.get("chars_used", 0) > metadata.get("max_chars", 4000):
        print("AVISO: contexto acima do limite.")
    if metadata.get("chunks_used", 0) > metadata.get("max_chunks", 8):
        print("AVISO: mais de 8 chunks.")
    if metadata.get("identity_cards_used", 0) > metadata.get("max_identity_cards", 3):
        print("AVISO: mais de 3 identity cards.")
    dedupe = metadata.get("dedupe") or {}
    removed = dedupe.get("removed") or {}
    if any(removed.values()):
        print(f"Duplicados removidos: {removed}")
    if metadata.get("fallback_without_memory"):
        print(f"AVISO: fallback sem memoria: {metadata.get('error')}")
    print("\n[FINAL PROMPT]\n")
    print(payload["final_prompt"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

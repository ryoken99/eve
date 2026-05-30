from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from core.memory_retrieval import format_memory_context, retrieve_memory_context


def print_results(question: str, top_k: int) -> None:
    payload = retrieve_memory_context(question, top_k=top_k, allow_private=True)
    if not payload.get("ok"):
        print(f"Retrieval falhou: {payload.get('error')}")
        return
    print(f"\nPergunta: {question}")
    print(f"Colecao: {payload.get('collection')}")
    print("\nTop chunks:")
    for index, item in enumerate(payload.get("results", []), start=1):
        print(f"\n[{index}] {item.source_file}")
        print(f"category={item.category} sensitivity={item.sensitivity} hybrid_score={item.hybrid_score:.3f}")
        print(item.public_dict()["excerpt"])
    print("\nContexto formatado:")
    print("-" * 72)
    print(format_memory_context(payload))
    print("-" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe terminal-only memory retrieval test for Eve.")
    parser.add_argument("--query", help="Run one query and exit.")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    if args.query:
        print_results(args.query, args.top_k)
        return 0

    print("Eve terminal memory test. Escreve uma pergunta ou 'exit'.")
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if question.lower() in {"exit", "quit", "/sair"}:
            return 0
        if not question:
            continue
        print_results(question, args.top_k)


if __name__ == "__main__":
    raise SystemExit(main())

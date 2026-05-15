from __future__ import annotations

import time

from runtime_validation_lib import append_runtime_jsonl, check, finalize

from memory.layered_memory import route_memory_item
from memory.vector_provider import rebuild_vector_memory, vector_prefetch


QUERIES = ["Mia Kinsky gym", "Codex computer use", "Wake on LAN", "manga dystopian", "magia mentalismo"]


def main() -> dict:
    seeds = [
        "Mia Kinsky gym treino e rotina de performance.",
        "Codex computer use usa DOM accessibility UIA antes de OCR.",
        "Wake on LAN permite acordar PC remotamente.",
        "manga dystopian com mundo dividido e escolhas morais.",
        "magia mentalismo como sistema de poderes narrativos.",
    ]
    for seed in seeds:
        route_memory_item(seed, metadata={"source": "vector_runtime"})
    started = time.perf_counter()
    rebuild = rebuild_vector_memory()
    elapsed = round(time.perf_counter() - started, 3)
    results = {query: vector_prefetch(query, limit=3) for query in QUERIES}
    append_runtime_jsonl("vector_memory", {"elapsed": elapsed, "results": results})
    checks = [
        check("vector rebuild returns index", bool(rebuild.get("index")), rebuild, critical=True),
        check("rebuild completes in bounded time", elapsed < 30, {"elapsed_seconds": elapsed}),
    ]
    for query, rows in results.items():
        checks.append(check(f"vector_prefetch returns results for {query}", bool(rows), {"count": len(rows), "sample": rows[:1]}, critical=True))
    return finalize("point_05_vector_memory_runtime", "Point 05 Vector Memory Runtime", "point_05_vector_memory_runtime.md", checks, {"elapsed_seconds": elapsed})


if __name__ == "__main__":
    main()

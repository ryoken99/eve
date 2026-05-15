from __future__ import annotations

from runtime_validation_lib import check, finalize

from memory.layered_memory import classify_memory_item, route_memory_item
from memory.memory_lifecycle import expire_memory, mark_conflict, promote_memory, register_memory
from memory.memory_manager import context_bundle


def main() -> dict:
    samples = [
        ("short", "Hoje ha um erro recente na janela ativa", {"temporary": True}),
        ("medium", "Projeto Eve runtime validation esta semana", {}),
        ("long", "Regra: Sandro prefere honestidade operacional sempre", {"stable": True}),
        ("archive", "duplicado sem valor futuro", {}),
    ]
    routed = [route_memory_item(text, metadata=meta) for _, text, meta in samples]
    registered = [register_memory(f"runtime memory {i}", layer="short_term", source="runtime", confidence=0.8) for i in range(5)]
    promoted = promote_memory(registered[0]["id"])
    expired = expire_memory(registered[1]["id"])
    conflict = mark_conflict(registered[2]["id"], registered[3]["id"])
    checks = [
        check("route_memory_item writes all samples", all(item.get("path") for item in routed), routed, critical=True),
        check("classification covers short term", classify_memory_item(samples[0][1], metadata=samples[0][2])["layer"] == "short_term", routed[0], critical=True),
        check("promotion moves memory upward", promoted["layer"] == "medium_term", promoted, critical=True),
        check("expiry archives memory", expired["layer"] == "archive_only" and expired["status"] == "archived", expired, critical=True),
        check("conflict marks memory IDs", bool(conflict.get("conflicted")), conflict),
        check("context bundle can be read", bool(context_bundle(max_chars=4000)), {"chars": len(context_bundle(max_chars=4000))}),
    ]
    return finalize("point_04_layered_memory_runtime", "Point 04 Layered Memory Runtime", "point_04_layered_memory_runtime.md", checks)


if __name__ == "__main__":
    main()

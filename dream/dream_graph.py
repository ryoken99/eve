from __future__ import annotations

from collections import defaultdict


def build_dream_graph(sources: dict[str, list[str]]) -> dict:
    edges = []
    topics: dict[str, set[str]] = defaultdict(set)
    for source, rows in sources.items():
        for row in rows:
            for token in row.lower().split():
                if len(token) > 4:
                    topics[token].add(source)
    for topic, seen in topics.items():
        if len(seen) >= 2:
            edges.append({"topic": topic, "sources": sorted(seen)})
    return {"nodes": sorted(sources), "edges": edges}

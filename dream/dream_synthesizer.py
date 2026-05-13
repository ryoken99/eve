from __future__ import annotations

from dream.dream_graph import build_dream_graph


def synthesize_dream(sources: dict[str, list[str]]) -> dict:
    graph = build_dream_graph(sources)
    connections = [f"{edge['topic']} liga {', '.join(edge['sources'])}" for edge in graph["edges"][:10]]
    return {
        "patterns": connections,
        "new_connections": graph["edges"],
        "possible_contradictions": [],
        "memory_moves": [],
        "lab_candidates": [{"topic": edge["topic"], "reason": "appears across multiple sources"} for edge in graph["edges"][:5]],
        "questions_for_sandro": [],
        "self_improvement_ideas": [],
    }

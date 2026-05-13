from __future__ import annotations


def experiment_template(kind: str, hypothesis: str) -> dict:
    templates = {
        "memory_retrieval": "compare semantic result relevance before and after change",
        "ui_action": "compare verified UI actions before and after router change",
        "research_quality": "compare dedupe and actionability scores",
        "self_update": "compile, test, and rollback if score drops",
        "error_reduction": "compare recurring error cluster count",
    }
    if kind not in templates:
        raise ValueError(f"unknown experiment template: {kind}")
    return {"kind": kind, "hypothesis": hypothesis, "procedure": templates[kind], "metric": f"{kind}_score", "threshold": 0.05}

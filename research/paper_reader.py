from __future__ import annotations


def summarize_paper(title: str, abstract: str, *, url: str = "") -> dict:
    lower = abstract.lower()
    return {
        "title": title,
        "url": url,
        "abstract": abstract,
        "method": "detected" if any(word in lower for word in ("method", "we propose", "approach")) else "not specified",
        "results": "detected" if any(word in lower for word in ("result", "outperform", "improve", "benchmark")) else "not specified",
        "limitations": "detected" if "limit" in lower else "not specified",
        "applicability_to_eve": "high" if any(word in lower for word in ("agent", "memory", "computer use", "ui")) else "watch",
    }

from __future__ import annotations


OFFICIAL_SOURCES = ("openai", "anthropic", "deepmind", "google", "meta", "x.ai", "arxiv", "huggingface", "github")


def source_quality(url: str, source: str = "") -> float:
    text = f"{url} {source}".lower()
    if any(item in text for item in OFFICIAL_SOURCES):
        return 0.9
    if text.startswith("https://"):
        return 0.65
    return 0.4

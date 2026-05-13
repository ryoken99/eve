from __future__ import annotations

import difflib


def dedupe_research_items(items: list[dict]) -> list[dict]:
    kept: list[dict] = []
    seen_urls = set()
    for item in items:
        url = item.get("url")
        title = item.get("title", "")
        if url and url in seen_urls:
            continue
        if any(difflib.SequenceMatcher(None, title.lower(), other.get("title", "").lower()).ratio() > 0.9 for other in kept):
            continue
        kept.append(item)
        if url:
            seen_urls.add(url)
    return kept

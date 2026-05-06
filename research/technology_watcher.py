from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from xml.etree import ElementTree

from core.paths import MEMORY_DIR, ensure_project_dirs


SOURCES = {
    "arxiv_ai": "https://export.arxiv.org/rss/cs.AI",
    "arxiv_cl": "https://export.arxiv.org/rss/cs.CL",
    "openai_blog": "https://openai.com/news/rss.xml",
}


def _strip(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    return text


def fetch_rss(url: str, limit: int = 5) -> list[dict]:
    with urllib.request.urlopen(url, timeout=20) as response:
        raw = response.read()
    root = ElementTree.fromstring(raw)
    items = []
    for item in root.findall(".//item")[:limit]:
        items.append(
            {
                "title": _strip(item.findtext("title", "")),
                "link": _strip(item.findtext("link", "")),
                "summary": _strip(item.findtext("description", ""))[:1000],
            }
        )
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns)[:limit]:
            link = entry.find("atom:link", ns)
            items.append(
                {
                    "title": _strip(entry.findtext("atom:title", "", ns)),
                    "link": link.attrib.get("href", "") if link is not None else "",
                    "summary": _strip(entry.findtext("atom:summary", "", ns))[:1000],
                }
            )
    return items


def run_technology_watch(limit_per_source: int = 3) -> Path:
    ensure_project_dirs()
    path = MEMORY_DIR / "technology" / "daily_technology_watch.md"
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    lines = [f"\n# Technology watch {timestamp}\n"]
    for name, url in SOURCES.items():
        lines.append(f"\n## {name}\n")
        try:
            items = fetch_rss(url, limit_per_source)
        except Exception as exc:
            lines.append(f"- erro: {exc}\n")
            continue
        for item in items:
            lines.append(f"- [{item['title']}]({item['link']})\n  {item['summary']}\n")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    return path

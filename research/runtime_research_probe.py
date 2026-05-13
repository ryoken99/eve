from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone

from core.paths import LOGS_DIR, ensure_project_dirs
from research.research_quality import score_research_item
from research.research_to_lab import research_to_lab_candidate


def fetch_research_signal(url: str, *, timeout: int = 15) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "EveRuntimeAudit/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(120000).decode("utf-8", errors="replace")
    return {"url": url, "status": response.status, "content_length": len(body), "sample": body[:2000]}


def run_runtime_research_probe() -> dict:
    ensure_project_dirs()
    sources = [
        "https://openai.com/research/",
        "https://export.arxiv.org/rss/cs.AI",
    ]
    fetched = []
    for url in sources:
        try:
            fetched.append(fetch_research_signal(url))
        except Exception as exc:
            fetched.append({"url": url, "status": None, "error": f"{type(exc).__name__}: {exc}", "content_length": 0, "sample": ""})
    items = []
    for row in fetched:
        title = "runtime technology research signal"
        sample = row.get("sample", "")
        if "agent" in sample.lower():
            title = "runtime AI agent research signal"
        scored = score_research_item({"title": title, "url": row["url"], "source": row["url"], "summary": sample[:1000]})
        candidate = research_to_lab_candidate(scored)
        items.append({"fetched": row, "scored": scored, "candidate": candidate})
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sources": sources,
        "items": items,
        "ok": any(item["fetched"].get("status") == 200 for item in items),
        "lab_ready": any((item["candidate"].get("expected_gain") or 0) > 0 for item in items),
    }
    path = LOGS_DIR / "research" / "runtime_research_probe.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    result["path"] = str(path)
    return result

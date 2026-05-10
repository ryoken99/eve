from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

from core.paths import LOGS_DIR, MEMORY_DIR, ensure_project_dirs
from tools.browser_human import close_browser_page, open_url, search_web


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for name, value in attrs:
            if name.lower() == "href" and value:
                self.links.append(value)


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered == "title":
            self._in_title = True
        if lowered in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "title":
            self._in_title = False
        if lowered in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        clean = " ".join(unescape(data).split())
        if not clean or self._skip_depth:
            return
        if self._in_title:
            self.title_parts.append(clean)
        self.text_parts.append(clean)

    @property
    def title(self) -> str:
        return " ".join(self.title_parts).strip()

    @property
    def text(self) -> str:
        return " ".join(self.text_parts).strip()


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _is_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _domain_allowed(url: str, allowed_domains: list[str] | None) -> bool:
    if not allowed_domains:
        return True
    host = urllib.parse.urlparse(url).netloc.lower()
    return any(host == domain.lower() or host.endswith("." + domain.lower()) for domain in allowed_domains)


def fetch_url(url: str, *, timeout: int = 20) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "EveResearchBot/0.1 (+local human-guided research)",
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        content_type = response.headers.get("content-type", "")
    encoding = "utf-8"
    match = re.search(r"charset=([\w.-]+)", content_type, flags=re.I)
    if match:
        encoding = match.group(1)
    html = raw.decode(encoding, errors="replace")
    parser = _TextParser()
    parser.feed(html)
    return {
        "url": url,
        "title": parser.title or urllib.parse.urlparse(url).path.rsplit("/", 1)[-1],
        "date": extract_date(parser.text),
        "text": parser.text,
        "html": html,
        "content_type": content_type,
    }


def extract_date(text: str) -> str:
    patterns = [
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s+20\d{2}\b",
        r"\b20\d{2}-\d{2}-\d{2}\b",
        r"\b\d{1,2}/\d{1,2}/20\d{2}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(0)
    return ""


def _parse_date(value: str) -> datetime | None:
    clean = value.strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    return None


def recent_enough_for_query(query: str, date_text: str, *, now: str | None = None) -> bool:
    lowered = query.lower()
    if "last 3 months" not in lowered and "ultimos 3 meses" not in lowered and "últimos 3 meses" not in lowered:
        return True
    parsed = _parse_date(date_text)
    if not parsed:
        return True
    today = datetime.strptime(now, "%Y-%m-%d") if now else datetime.now()
    return parsed >= today - timedelta(days=92)


def extract_links(html: str, base_url: str, *, allowed_domains: list[str] | None = None) -> list[str]:
    parser = _LinkParser()
    parser.feed(html)
    seen: set[str] = set()
    links: list[str] = []
    for href in parser.links:
        absolute = urllib.parse.urljoin(base_url, href.split("#", 1)[0])
        if not _is_url(absolute) or not _domain_allowed(absolute, allowed_domains):
            continue
        if absolute not in seen:
            seen.add(absolute)
            links.append(absolute)
    return links


def candidate_article_links(links: list[str]) -> list[str]:
    blocked_exact_paths = {"", "/", "/research", "/news", "/economic-futures", "/learn", "/jobs"}
    blocked_prefixes = ("/research/team/", "/claude/", "/features/")
    candidates: list[str] = []
    seen: set[str] = set()
    for url in links:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.rstrip("/")
        if path in blocked_exact_paths or any(path.startswith(prefix.rstrip("/")) for prefix in blocked_prefixes):
            continue
        if "/research/" not in path:
            continue
        if url not in seen:
            seen.add(url)
            candidates.append(url)
    return candidates


def _sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if len(item.strip()) > 40]


def _query_terms(query: str) -> list[str]:
    stop = {"the", "and", "for", "com", "uma", "uns", "dos", "das", "que", "sobre", "research", "papers"}
    return [term.lower() for term in re.findall(r"[\w-]{4,}", query) if term.lower() not in stop]


def _best_claim(text: str, query: str) -> str:
    terms = _query_terms(query)
    candidates = _sentences(text)
    if not candidates:
        return text[:280].strip()
    ranked = sorted(
        candidates,
        key=lambda sentence: sum(1 for term in terms if term in sentence.lower()),
        reverse=True,
    )
    return ranked[0][:500]


def build_research_report_from_pages(query: str, pages: list[dict]) -> dict:
    source_facts = []
    for page in pages:
        text = " ".join((page.get("text") or "").split())
        if not text:
            continue
        claim = _best_claim(text, query)
        source_facts.append(
            {
                "title": page.get("title") or page.get("url", ""),
                "url": page.get("url", ""),
                "date": page.get("date", ""),
                "claim": claim,
                "quote": claim[:280],
                "confidence": 0.85 if page.get("date") else 0.72,
            }
        )

    interpretation = [
        {
            "summary": "Relatorio auditavel criado a partir de fontes recolhidas, mantendo factos extraidos separados da interpretacao da Eve.",
            "uncertainty": "A qualidade depende da extracao HTML e da cobertura das paginas candidatas; OCR visual serve como evidencia de navegacao, nao como unica fonte.",
            "reasoning": "Separar source_facts de eve_interpretation reduz alucinacao subtil e facilita revisao humana.",
        }
    ]
    return {
        "query": query,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_facts": source_facts,
        "eve_interpretation": interpretation,
        "limitations": [
            "Nem todos os sites expõem datas ou texto limpo em HTML.",
            "A navegacao visual confirma o contexto humano, mas artigos longos devem ser extraidos por fonte estruturada quando possivel.",
        ],
    }


def _write_markdown(report: dict, path: Path) -> None:
    lines = [
        f"# Web research report: {report['query']}",
        "",
        f"Created: {report['created_at']}",
        "",
        "## Source facts",
        "",
    ]
    for index, fact in enumerate(report["source_facts"], start=1):
        lines.extend(
            [
                f"### {index}. {fact['title']}",
                "",
                f"- URL: {fact['url']}",
                f"- Date: {fact.get('date') or 'unknown'}",
                f"- Confidence: {fact['confidence']}",
                f"- Claim: {fact['claim']}",
                f"- Evidence excerpt: {fact['quote']}",
                "",
            ]
        )
    lines.extend(["## Eve interpretation", ""])
    for item in report["eve_interpretation"]:
        lines.extend(
            [
                f"- Summary: {item['summary']}",
                f"- Uncertainty: {item['uncertainty']}",
                f"- Reasoning: {item['reasoning']}",
                "",
            ]
        )
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def save_research_report(report: dict) -> dict:
    ensure_project_dirs()
    report_dir = LOGS_DIR / "research"
    report_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", report["query"].lower()).strip("-")[:60] or "research"
    base = report_dir / f"{_now_stamp()}_{slug}"
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown(report, md_path)

    memory_path = MEMORY_DIR / "technology" / "research_reports.md"
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    with memory_path.open("a", encoding="utf-8") as handle:
        handle.write(f"- {report['created_at']}: {report['query']} -> {md_path}\n")
    return {"json": str(json_path), "markdown": str(md_path), "memory_index": str(memory_path)}


def run_web_research_report(
    query: str,
    *,
    seed_urls: list[str] | None = None,
    allowed_domains: list[str] | None = None,
    max_pages: int = 8,
    open_visible_browser: bool = True,
) -> dict:
    if not query.strip():
        raise ValueError("query vazia")
    ensure_project_dirs()
    browser_evidence = None
    browser_closed = None
    try:
        if open_visible_browser:
            browser_evidence = search_web(query)

        seeds = list(seed_urls or [])
        if not seeds and _is_url(query):
            seeds.append(query)
        pages: list[dict] = []
        seed_pages: list[dict] = []
        candidates: list[str] = []
        failures: list[dict] = []

        for seed in seeds:
            try:
                if open_visible_browser:
                    open_url(seed)
                page = fetch_url(seed)
                seed_pages.append({key: value for key, value in page.items() if key != "html"})
                candidates.extend(candidate_article_links(extract_links(page["html"], seed, allowed_domains=allowed_domains)))
            except Exception as exc:
                failures.append({"url": seed, "error": f"{type(exc).__name__}: {exc}"})

        for url in candidates:
            if len(pages) >= max_pages:
                break
            try:
                page = fetch_url(url)
                text = page.get("text", "")
                if recent_enough_for_query(query, page.get("date", "")) and any(
                    term in text.lower() or term in page.get("title", "").lower() for term in _query_terms(query)
                ):
                    pages.append({key: value for key, value in page.items() if key != "html"})
            except Exception as exc:
                failures.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})

        if not pages:
            pages = seed_pages[:max_pages]

        report = build_research_report_from_pages(query, pages)
        report["browser_evidence"] = browser_evidence
        report["seed_urls"] = seeds
        report["allowed_domains"] = allowed_domains or []
        report["failed_pages"] = failures[:10]
        paths = save_research_report(report)
        result = {"status": "ok", "report": report, "paths": paths}
    finally:
        if open_visible_browser:
            browser_closed = close_browser_page("web_research_finished")
    if browser_closed is not None:
        result["browser_closed"] = browser_closed
    return result

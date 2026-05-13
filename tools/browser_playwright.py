from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BrowserActionResult:
    ok: bool
    engine: str
    action: str
    detail: dict


def _sync_playwright():
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        return sync_playwright
    except Exception:
        return None


def playwright_available() -> bool:
    return _sync_playwright() is not None


def browser_dom_snapshot(page: Any | None = None) -> dict:
    """Return a structured browser snapshot.

    When a Playwright page is supplied, this reads from DOM/accessibility data.
    Without a page, it reports availability so callers can route to another
    engine without pretending DOM control happened.
    """

    if page is None:
        return {"available": playwright_available(), "engine": "playwright", "attached": False, "elements": []}
    title = ""
    url = ""
    text = ""
    try:
        title = page.title()
        url = page.url
        text = page.locator("body").inner_text(timeout=2000)
    except Exception as exc:
        return {"available": True, "engine": "playwright", "attached": True, "ok": False, "error": str(exc)}
    return {"available": True, "engine": "playwright", "attached": True, "ok": True, "title": title, "url": url, "text": text[:20000]}


def click_by_role(role: str, name: str, *, page: Any | None = None) -> dict:
    if page is None:
        return BrowserActionResult(False, "playwright", "click_by_role", {"reason": "no playwright page attached", "role": role, "name": name}).__dict__
    try:
        page.get_by_role(role, name=name).click(timeout=3000)
        return BrowserActionResult(True, "playwright", "click_by_role", {"role": role, "name": name}).__dict__
    except Exception as exc:
        return BrowserActionResult(False, "playwright", "click_by_role", {"role": role, "name": name, "error": str(exc)}).__dict__


def fill_by_label(label: str, text: str, *, page: Any | None = None) -> dict:
    if page is None:
        return BrowserActionResult(False, "playwright", "fill_by_label", {"reason": "no playwright page attached", "label": label}).__dict__
    try:
        page.get_by_label(label).fill(text, timeout=3000)
        return BrowserActionResult(True, "playwright", "fill_by_label", {"label": label, "text_length": len(text)}).__dict__
    except Exception as exc:
        return BrowserActionResult(False, "playwright", "fill_by_label", {"label": label, "error": str(exc)}).__dict__

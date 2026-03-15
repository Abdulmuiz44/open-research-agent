"""Bounded discovery + fetch pipeline helpers."""

from __future__ import annotations

import asyncio
import re

from src.core.config import get_settings
from src.core.logging import get_logger
from src.data.models import CandidateSource, FetchedDocument
from src.search.provider import SearchProvider
from src.search.ranker import rank_sources
from src.web.fetch_browser import fetch_via_browser
from src.web.fetch_http import fetch_via_http


def _looks_js_heavy(html: str) -> bool:
    markers = [
        "__next",
        "data-reactroot",
        "ng-version",
        "window.__INITIAL_STATE__",
        "id=\"app\"",
        "enable javascript",
    ]
    lowered = html.lower()
    return any(marker.lower() in lowered for marker in markers)


def should_use_browser_fallback(document: FetchedDocument, min_text_chars: int) -> str | None:
    """Return reason string if bounded browser fallback should run, else None."""
    if document.fetch_method == "browser":
        return None

    if not document.success:
        if document.status_code in {401, 403, 429, 503}:
            return f"http_blocked_status_{document.status_code}"
        return None

    html = document.raw_html or ""
    if not html.strip():
        return "empty_html"

    visible_text = re.sub(r"<[^>]+>", " ", html)
    visible_text = re.sub(r"\s+", " ", visible_text).strip()
    if len(visible_text) < min_text_chars:
        return "near_empty_content"

    if _looks_js_heavy(html) and len(visible_text) < (min_text_chars * 2):
        return "js_heavy_page_marker"

    return None


class Crawler:
    """Coordinates bounded discovery and HTTP fetch with optional browser fallback."""

    def __init__(self, provider: SearchProvider) -> None:
        self.provider = provider
        self.settings = get_settings()
        self.logger = get_logger("ora.crawler")

    def discover(self, run_id: str, queries: list[str]) -> list[CandidateSource]:
        """Discover and rank candidate sources from provider results."""
        candidates: list[CandidateSource] = []
        for query in queries:
            candidates.extend(self.provider.search(run_id=run_id, query=query, limit=self.settings.max_sources_per_run))
        return rank_sources(candidates, top_n=self.settings.max_sources_per_run)

    async def fetch_one(self, source: CandidateSource) -> FetchedDocument:
        """Fetch one source over HTTP, then apply bounded browser fallback if needed."""
        http_doc = await fetch_via_http(source)
        reason = should_use_browser_fallback(http_doc, self.settings.browser_fallback_min_text_chars)
        if not self.settings.browser_fallback_enabled or reason is None:
            return http_doc

        self.logger.info("browser fallback triggered | source_id=%s reason=%s", source.id, reason)
        browser_doc = await fetch_via_browser(source)
        browser_doc.fallback_triggered = True
        browser_doc.fallback_reason = reason
        return browser_doc

    async def fetch(self, sources: list[CandidateSource]) -> list[FetchedDocument]:
        """Fetch a bounded number of sources with selective browser fallback."""
        limited = sources[: self.settings.max_fetch_per_run]
        tasks = [self.fetch_one(source) for source in limited]
        return await asyncio.gather(*tasks)

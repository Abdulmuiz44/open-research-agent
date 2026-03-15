"""Bounded discovery + fetch pipeline helpers."""

from __future__ import annotations

import asyncio

from src.core.config import get_settings
from src.data.models import CandidateSource, FetchedDocument
from src.search.provider import SearchProvider
from src.search.ranker import rank_sources
from src.web.fetch_browser import fetch_via_browser
from src.web.fetch_http import fetch_via_http


class Crawler:
    """Coordinates bounded discovery and fetch under simple constraints."""

    def __init__(self, provider: SearchProvider) -> None:
        self.provider = provider
        self.settings = get_settings()

    def discover(self, run_id: str, queries: list[str]) -> list[CandidateSource]:
        """Discover and rank candidate sources from provider results."""
        candidates: list[CandidateSource] = []
        for query in queries:
            candidates.extend(self.provider.search(run_id=run_id, query=query, limit=self.settings.max_sources_per_run))
        return rank_sources(candidates, top_n=self.settings.max_sources_per_run)

    async def fetch(self, sources: list[CandidateSource]) -> list[FetchedDocument]:
        """Fetch a bounded number of sources via HTTP with browser fallback when marked."""
        limited = sources[: self.settings.max_fetch_per_run]
        return [await self._fetch_one(source) for source in limited]

    async def _fetch_one(self, source: CandidateSource) -> FetchedDocument:
        fetched = await fetch_via_http(source)
        if not fetched.success and self._should_use_browser_fallback(source=source, fetched=fetched):
            return await fetch_via_browser(source)
        return fetched

    def _should_use_browser_fallback(self, *, source: CandidateSource, fetched: FetchedDocument) -> bool:
        """Allow explicit, bounded browser fallback for known JS-heavy sources."""
        if fetched.success:
            return False
        if source.metadata.get("browser_required") is True:
            return True
        if fetched.status_code in {403, 429}:
            return True
        return False

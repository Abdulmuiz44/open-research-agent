"""Bounded discovery + fetch pipeline helpers."""

from __future__ import annotations

import asyncio

from src.core.config import get_settings
from src.data.models import CandidateSource, FetchedDocument
from src.search.provider import SearchProvider
from src.search.ranker import rank_sources
from src.web.fetch_http import fetch_via_http


class Crawler:
    """Coordinates bounded discovery and HTTP fetch under simple constraints."""

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
        """Fetch a bounded number of sources via HTTP."""
        limited = sources[: self.settings.max_fetch_per_run]
        tasks = [fetch_via_http(source) for source in limited]
        return await asyncio.gather(*tasks)

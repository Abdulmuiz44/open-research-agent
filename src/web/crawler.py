"""Bounded crawler skeleton for URL acquisition workflows."""

from __future__ import annotations

from src.data.models import CandidateSource


class Crawler:
    """Coordinates crawl operations under bounded constraints."""

    async def crawl(self, seeds: list[str], max_pages: int) -> list[CandidateSource]:
        """Crawl from seed URLs and produce candidate sources."""
        # TODO: Integrate Crawl4AI with allowlist/denylist constraints.
        raise NotImplementedError

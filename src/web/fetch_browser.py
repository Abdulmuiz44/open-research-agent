"""Browser-based fetch fallback skeleton."""

from __future__ import annotations

from src.data.models import CandidateSource, FetchedDocument


async def fetch_via_browser(source: CandidateSource) -> FetchedDocument:
    """Fetch a source via browser rendering when HTTP extraction fails."""
    # TODO: Implement Playwright fallback fetch path.
    raise NotImplementedError

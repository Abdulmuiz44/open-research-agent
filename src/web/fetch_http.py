"""HTTP fetcher skeleton for acquiring web content."""

from __future__ import annotations

from src.data.models import CandidateSource, FetchedDocument


async def fetch_via_http(source: CandidateSource) -> FetchedDocument:
    """Fetch a source with HTTP-first strategy."""
    # TODO: Implement httpx fetch with retries, timeout, and metadata capture.
    raise NotImplementedError

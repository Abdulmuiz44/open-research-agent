"""Browser-based fetch fallback shell."""

from __future__ import annotations

from src.data.models import CandidateSource, FetchedDocument


async def fetch_via_browser(source: CandidateSource) -> FetchedDocument:
    """Return a bounded placeholder result until browser automation is enabled."""
    return FetchedDocument(
        run_id=source.run_id,
        source_id=source.id,
        requested_url=source.url,
        fetch_method="browser",
        success=False,
        error="browser_fetch_not_enabled",
    )

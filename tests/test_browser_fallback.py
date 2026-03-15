import asyncio

from src.data.models import CandidateSource
from src.web.fetch_browser import fetch_via_browser


def test_browser_fallback_placeholder_shape() -> None:
    source = CandidateSource(
        run_id="run-1",
        query="q",
        url="https://example.com",
        domain="example.com",
        provider="test",
        provider_rank=1,
    )

    result = asyncio.run(fetch_via_browser(source))
    assert result.fetch_method == "browser"
    assert result.success is False
    assert result.error == "browser_fetch_not_enabled"

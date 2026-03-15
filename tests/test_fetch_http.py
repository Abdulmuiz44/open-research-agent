import asyncio

from src.data.models import CandidateSource
from src.web.fetch_http import fetch_via_http


def test_fetch_http_result_shape() -> None:
    source = CandidateSource(
        run_id="run-1",
        query="q",
        url="https://example.com",
        domain="example.com",
        provider="test",
        provider_rank=1,
    )
    result = asyncio.run(fetch_via_http(source))
    assert result.run_id == source.run_id
    assert result.source_id == source.id
    assert result.fetch_method == "http"
    assert result.success in {True, False}

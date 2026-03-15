from __future__ import annotations

import asyncio

from src.data.models import CandidateSource, FetchedDocument
from src.search.provider import StubSearchProvider
from src.web.crawler import Crawler


def test_browser_fallback_decision_true_for_marked_source() -> None:
    crawler = Crawler(provider=StubSearchProvider())
    source = CandidateSource(
        run_id="run-1",
        query="q",
        url="https://example.com",
        domain="example.com",
        provider="test",
        provider_rank=1,
        metadata={"browser_required": True},
    )
    fetched = FetchedDocument(run_id="run-1", source_id=source.id, requested_url=source.url, success=False, status_code=403)
    assert crawler._should_use_browser_fallback(source=source, fetched=fetched) is True


def test_browser_fallback_decision_false_for_success() -> None:
    crawler = Crawler(provider=StubSearchProvider())
    source = CandidateSource(run_id="run-1", query="q", url="https://example.com", domain="example.com", provider="test", provider_rank=1)
    fetched = FetchedDocument(run_id="run-1", source_id=source.id, requested_url=source.url, success=True, status_code=200)
    assert crawler._should_use_browser_fallback(source=source, fetched=fetched) is False

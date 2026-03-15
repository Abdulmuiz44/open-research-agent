from __future__ import annotations

import asyncio

from src.data.models import CandidateSource, FetchMethod, FetchOutcome, FetchedDocument
from src.search.provider import StubSearchProvider
from src.web import crawler as crawler_module
from src.web.crawler import Crawler, should_use_browser_fallback


def _source() -> CandidateSource:
    return CandidateSource(
        run_id="run-1",
        query="q",
        url="https://example.com/page",
        domain="example.com",
        provider="test",
        provider_rank=1,
    )


def test_should_use_browser_fallback_for_near_empty_success() -> None:
    doc = FetchedDocument(
        run_id="run-1",
        source_id="s1",
        requested_url="https://example.com",
        raw_html="<html><body><div>tiny</div></body></html>",
        success=True,
        fetch_method=FetchMethod.HTTP,
        fetch_outcome=FetchOutcome.SUCCESS,
    )
    reason = should_use_browser_fallback(doc, min_text_chars=50)
    assert reason == "near_empty_content"


def test_should_use_browser_fallback_for_blocked_status() -> None:
    doc = FetchedDocument(
        run_id="run-1",
        source_id="s1",
        requested_url="https://example.com",
        status_code=403,
        success=False,
        fetch_method=FetchMethod.HTTP,
        fetch_outcome=FetchOutcome.HTTP_ERROR,
    )
    reason = should_use_browser_fallback(doc, min_text_chars=50)
    assert reason == "http_blocked_status_403"


def test_crawler_uses_browser_when_http_insufficient(monkeypatch) -> None:
    source = _source()
    crawler = Crawler(StubSearchProvider())

    async def fake_http(_source: CandidateSource) -> FetchedDocument:
        return FetchedDocument(
            run_id=source.run_id,
            source_id=source.id,
            requested_url=source.url,
            raw_html="<html><body><div id='app'></div></body></html>",
            success=True,
            fetch_method=FetchMethod.HTTP,
            fetch_outcome=FetchOutcome.SUCCESS,
        )

    async def fake_browser(_source: CandidateSource) -> FetchedDocument:
        return FetchedDocument(
            run_id=source.run_id,
            source_id=source.id,
            requested_url=source.url,
            raw_html="<html><body><main>rendered content with enough text to be useful" + (" x" * 400) + "</main></body></html>",
            success=True,
            fetch_method=FetchMethod.BROWSER,
            fetch_outcome=FetchOutcome.SUCCESS,
            rendered_content_available=True,
        )

    monkeypatch.setattr(crawler_module, "fetch_via_http", fake_http)
    monkeypatch.setattr(crawler_module, "fetch_via_browser", fake_browser)
    monkeypatch.setattr(crawler.settings, "browser_fallback_enabled", True)
    monkeypatch.setattr(crawler.settings, "browser_fallback_min_text_chars", 200)

    result = asyncio.run(crawler.fetch_one(source))
    assert result.fetch_method == FetchMethod.BROWSER
    assert result.fallback_triggered is True
    assert result.fallback_reason

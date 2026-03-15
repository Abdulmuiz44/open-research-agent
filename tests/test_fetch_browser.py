from __future__ import annotations

import asyncio

from src.data.models import CandidateSource, FetchMethod
from src.web import fetch_browser as fetch_browser_module
from src.web.fetch_browser import fetch_via_browser


class _FakeResponse:
    status = 200


class _FakePage:
    url = "https://example.com/final"

    async def goto(self, *_args, **_kwargs):
        return _FakeResponse()

    async def wait_for_timeout(self, _ms: int) -> None:
        return None

    async def content(self) -> str:
        return "<html><head><title>Rendered</title></head><body><main>rendered text</main></body></html>"

    async def title(self) -> str:
        return "Rendered"


class _FakeContext:
    async def new_page(self):
        return _FakePage()

    async def close(self) -> None:
        return None


class _FakeBrowser:
    async def new_context(self, **_kwargs):
        return _FakeContext()

    async def close(self) -> None:
        return None


class _FakeChromium:
    async def launch(self, **_kwargs):
        return _FakeBrowser()


class _FakePlaywright:
    chromium = _FakeChromium()


class _FakeManager:
    async def __aenter__(self):
        return _FakePlaywright()

    async def __aexit__(self, exc_type, exc, tb):
        return None


def test_fetch_via_browser_success(monkeypatch) -> None:
    source = CandidateSource(
        run_id="run-1",
        query="q",
        url="https://example.com",
        domain="example.com",
        provider="test",
        provider_rank=1,
    )
    monkeypatch.setattr(fetch_browser_module, "async_playwright", lambda: _FakeManager())
    result = asyncio.run(fetch_via_browser(source))
    assert result.success is True
    assert result.fetch_method == FetchMethod.BROWSER
    assert result.rendered_content_available is True


def test_fetch_via_browser_unavailable(monkeypatch) -> None:
    source = CandidateSource(
        run_id="run-1",
        query="q",
        url="https://example.com",
        domain="example.com",
        provider="test",
        provider_rank=1,
    )

    class BrokenManager:
        async def __aenter__(self):
            raise OSError("no browser")

        async def __aexit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr(fetch_browser_module, "async_playwright", lambda: BrokenManager())
    result = asyncio.run(fetch_via_browser(source))
    assert result.success is False
    assert result.fetch_method == FetchMethod.BROWSER
    assert "browser_failed" in (result.error or "")

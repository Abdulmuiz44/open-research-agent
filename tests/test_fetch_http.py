import asyncio

import httpx

from src.data.models import CandidateSource
from src.web.fetch_http import fetch_via_http


class _MockResponse:
    def __init__(self, status_code: int = 200, text: str = "<html>ok</html>", url: str = "https://example.com") -> None:
        self.status_code = status_code
        self.text = text
        self.url = url
        self.headers = {"content-type": "text/html", "content-length": str(len(text))}


class _MockClient:
    def __init__(self, response: _MockResponse | None = None, exc: Exception | None = None) -> None:
        self._response = response
        self._exc = exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def get(self, _url: str):
        if self._exc:
            raise self._exc
        return self._response


def test_fetch_http_result_shape(monkeypatch) -> None:
    source = CandidateSource(run_id="run-1", query="q", url="https://example.com", domain="example.com", provider="test", provider_rank=1)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: _MockClient(response=_MockResponse()))
    result = asyncio.run(fetch_via_http(source))
    assert result.run_id == source.run_id
    assert result.source_id == source.id
    assert result.fetch_method == "http"
    assert result.success is True


def test_fetch_http_handles_failures(monkeypatch) -> None:
    source = CandidateSource(run_id="run-1", query="q", url="https://example.com", domain="example.com", provider="test", provider_rank=1)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: _MockClient(exc=httpx.ConnectError("boom")))
    result = asyncio.run(fetch_via_http(source))
    assert result.success is False
    assert result.error

"""HTTP fetcher for acquiring web content."""

from __future__ import annotations

import asyncio

import httpx

from src.core.config import get_settings
from src.data.models import CandidateSource, FetchedDocument


async def fetch_via_http(source: CandidateSource) -> FetchedDocument:
    """Fetch a source with HTTP-first strategy."""
    settings = get_settings()
    headers = {"user-agent": settings.user_agent, "accept": "text/html, text/plain"}
    timeout = settings.request_timeout_seconds

    error: str | None = None
    for _attempt in range(settings.request_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
                response = await client.get(str(source.url))

            content_type = response.headers.get("content-type")
            content_length = response.headers.get("content-length")
            return FetchedDocument(
                run_id=source.run_id,
                source_id=source.id,
                requested_url=source.url,
                final_url=str(response.url),
                status_code=response.status_code,
                content_type=content_type,
                content_length=int(content_length) if content_length and content_length.isdigit() else None,
                text=response.text if "text/plain" in (content_type or "") else None,
                raw_html=response.text,
                fetch_method="http",
                success=response.status_code < 400,
                error=None if response.status_code < 400 else f"http_{response.status_code}",
            )
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            error = str(exc)
            await asyncio.sleep(0.1)

    return FetchedDocument(
        run_id=source.run_id,
        source_id=source.id,
        requested_url=source.url,
        fetch_method="http",
        success=False,
        error=error or "fetch_failed",
    )

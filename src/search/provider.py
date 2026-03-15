"""Search provider interfaces and local provider implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

import httpx
from selectolax.parser import HTMLParser

from src.core.config import Settings
from src.data.models import CandidateSource


class SearchProvider(Protocol):
    """Protocol for search provider adapters."""

    def search(self, run_id: str, query: str, limit: int = 10) -> list[CandidateSource]:
        """Execute a search query and return candidate sources."""


@dataclass(slots=True)
class DuckDuckGoHtmlProvider:
    """Simple DuckDuckGo HTML search provider for local usage."""

    timeout_s: float
    user_agent: str
    endpoint: str = "https://duckduckgo.com/html/"

    def search(self, run_id: str, query: str, limit: int = 10) -> list[CandidateSource]:
        headers = {"user-agent": self.user_agent}
        with httpx.Client(timeout=self.timeout_s, follow_redirects=True, headers=headers) as client:
            response = client.get(self.endpoint, params={"q": query})
            response.raise_for_status()

        tree = HTMLParser(response.text)
        results: list[CandidateSource] = []
        for rank, node in enumerate(tree.css(".result"), start=1):
            link = node.css_first("a.result__a")
            if link is None:
                continue

            href = link.attributes.get("href", "").strip()
            if not href.startswith("http"):
                continue

            snippet_node = node.css_first(".result__snippet")
            snippet = snippet_node.text(strip=True) if snippet_node else None
            domain = urlparse(href).netloc.lower()

            results.append(
                CandidateSource(
                    run_id=run_id,
                    query=query,
                    url=href,
                    domain=domain,
                    title=link.text(strip=True),
                    snippet=snippet,
                    provider="duckduckgo_html",
                    provider_rank=rank,
                    score=max(0.0, 1 - (rank - 1) * 0.05),
                    metadata={"endpoint": self.endpoint},
                )
            )
            if len(results) >= limit:
                break

        return results


class StubSearchProvider:
    """Fallback provider used when discovery is intentionally disabled."""

    def search(self, run_id: str, query: str, limit: int = 10) -> list[CandidateSource]:
        _ = (run_id, query, limit)
        return []


def build_search_provider(settings: Settings) -> SearchProvider:
    """Build provider from runtime configuration."""
    if settings.search_provider == "duckduckgo_html":
        return DuckDuckGoHtmlProvider(
            timeout_s=settings.request_timeout_seconds,
            user_agent=settings.user_agent,
            endpoint=settings.search_endpoint,
        )
    return StubSearchProvider()

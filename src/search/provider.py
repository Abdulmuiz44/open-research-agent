"""Search provider interfaces and placeholder implementations."""

from __future__ import annotations

from typing import Protocol

from src.data.models import CandidateSource


class SearchProvider(Protocol):
    """Protocol for search provider adapters."""

    def search(self, query: str, limit: int = 10) -> list[CandidateSource]:
        """Execute a search query and return candidate sources."""


class StubSearchProvider:
    """Temporary search provider placeholder for scaffold stage."""

    def search(self, query: str, limit: int = 10) -> list[CandidateSource]:
        """Return no sources until a concrete adapter is implemented."""
        # TODO: Replace with real provider integration.
        return []

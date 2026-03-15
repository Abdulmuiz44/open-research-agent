"""Candidate source ranking and deduplication helpers."""

from __future__ import annotations

from urllib.parse import urlparse

from src.data.models import CandidateSource


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"


def deduplicate_sources(sources: list[CandidateSource]) -> list[CandidateSource]:
    """Deduplicate sources by normalized URL keeping best score."""
    deduped: dict[str, CandidateSource] = {}
    for source in sources:
        key = _canonical_url(str(source.url))
        existing = deduped.get(key)
        if existing is None or source.score > existing.score:
            deduped[key] = source
    return list(deduped.values())


def rank_sources(sources: list[CandidateSource], top_n: int = 10) -> list[CandidateSource]:
    """Rank candidate sources with lightweight deterministic heuristics."""
    rescored: list[CandidateSource] = []
    for source in sources:
        score = source.score
        score += max(0, 1.0 - (source.provider_rank * 0.05))
        if source.title:
            score += 0.2
        if source.snippet:
            score += 0.2
        if source.domain.endswith(".gov") or source.domain.endswith(".edu"):
            score += 0.15
        source.score = round(score, 4)
        rescored.append(source)

    ordered = sorted(
        deduplicate_sources(rescored),
        key=lambda item: (-item.score, item.provider_rank, item.domain),
    )
    return ordered[:top_n]

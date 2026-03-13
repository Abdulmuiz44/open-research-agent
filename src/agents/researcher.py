"""Researcher agent skeleton for source discovery and acquisition coordination."""

from __future__ import annotations

from src.data.models import CandidateSource, ResearchPlan


class ResearcherAgent:
    """Coordinates search, fetch, and extraction stages for a plan."""

    def discover_sources(self, plan: ResearchPlan) -> list[CandidateSource]:
        """Discover candidate sources for plan queries."""
        # TODO: Connect search provider, deduplication, and ranking.
        raise NotImplementedError

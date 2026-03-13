"""Search query planning helpers."""

from __future__ import annotations

from src.data.models import ResearchPlan


def build_queries(plan: ResearchPlan) -> list[str]:
    """Convert a plan into executable search queries."""
    # TODO: Add deterministic query expansion and normalization.
    return plan.search_queries

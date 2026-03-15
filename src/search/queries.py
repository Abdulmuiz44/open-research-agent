"""Search query planning helpers."""

from __future__ import annotations

import re

from src.data.models import ResearchPlan


def normalize_query(text: str) -> str:
    """Normalize query text deterministically."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return re.sub(r"[^\w\s\-:/.]", "", normalized)


def build_queries(plan: ResearchPlan) -> list[str]:
    """Convert plan objectives into a bounded query list."""
    seeds = [plan.objective, *plan.research_objectives, *plan.search_queries]
    queries: list[str] = []
    seen: set[str] = set()

    for seed in seeds:
        query = normalize_query(seed)
        if query and query not in seen:
            seen.add(query)
            queries.append(query)

        # lightweight expansion with evidence-focused variant
        if query:
            variant = f"{query} data evidence"
            if variant not in seen:
                seen.add(variant)
                queries.append(variant)

        if len(queries) >= 6:
            break

    return queries[:6]

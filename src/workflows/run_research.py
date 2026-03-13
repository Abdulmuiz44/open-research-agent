"""Pipeline orchestration skeleton for end-to-end research runs."""

from __future__ import annotations

from src.data.models import Report, ResearchRequest


class ResearchWorkflow:
    """Coordinates bounded research stages from request to report."""

    def run(self, request: ResearchRequest) -> Report:
        """Execute research workflow stages in sequence."""
        # TODO: Orchestrate planner, search, fetch, extraction, analysis, and reporting.
        raise NotImplementedError

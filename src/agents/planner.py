"""Planner agent skeleton for generating bounded research plans."""

from __future__ import annotations

from src.data.models import ResearchRequest, ResearchPlan


class PlannerAgent:
    """Creates bounded plans from incoming research requests."""

    def create_plan(self, request: ResearchRequest) -> ResearchPlan:
        """Build a plan with sub-questions, queries, and stopping rules."""
        # TODO: Implement planner strategy using LLM router + deterministic guards.
        raise NotImplementedError

"""Pipeline orchestration shell for bounded research runs."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.core.exceptions import NotImplementedWorkflowError
from src.data.models import ResearchRun


class RunResearchInput(BaseModel):
    """Inputs required to kick off a bounded research workflow run."""

    objective: str = Field(min_length=3)
    constraints: list[str] = Field(default_factory=list)
    max_sources: int = Field(default=10, ge=1, le=100)


class RunResearchOutput(BaseModel):
    """Top-level workflow output placeholder for run metadata."""

    run: ResearchRun
    message: str


def initialize_run(payload: RunResearchInput) -> ResearchRun:
    """Create initial run metadata before stage orchestration."""
    return ResearchRun(objective=payload.objective)


def run_research_workflow(payload: RunResearchInput) -> RunResearchOutput:
    """Workflow contract shell; real orchestration is intentionally deferred."""
    run = initialize_run(payload)
    raise NotImplementedWorkflowError(
        f"Research workflow orchestration is not implemented yet for run {run.id}."
    )

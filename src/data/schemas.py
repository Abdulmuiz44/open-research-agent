"""API and interface schemas derived from core data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResearchRunCreateRequest(BaseModel):
    """Request payload for creating a research run."""

    objective: str = Field(min_length=3)
    constraints: list[str] = Field(default_factory=list)
    max_sources: int = Field(default=10, ge=1, le=100)


class ResearchRunResponse(BaseModel):
    """Response payload exposing run lifecycle metadata."""

    run_id: str
    status: str

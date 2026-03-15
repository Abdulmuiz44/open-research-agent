"""API and interface schemas derived from core data models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.data.models import ArtifactReference, RunStatus


class HealthResponse(BaseModel):
    """Health-check response payload."""

    status: str = "ok"
    app_name: str
    environment: str


class ResearchRunCreateRequest(BaseModel):
    """Request payload for creating a research run."""

    objective: str = Field(min_length=3)
    constraints: list[str] = Field(default_factory=list)
    max_sources: int = Field(default=10, ge=1, le=100)


class ResearchRunResponse(BaseModel):
    """Response payload exposing run lifecycle metadata and report summaries."""

    run_id: str
    objective: str
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    message: str | None = None
    search_queries: list[str] = Field(default_factory=list)
    source_count: int = 0
    fetched_count: int = 0
    extracted_count: int = 0
    finding_count: int = 0
    artifact_count: int = 0
    artifact_dir: str | None = None
    report_artifact: ArtifactReference | None = None
    artifact_summary: dict[str, int] = Field(default_factory=dict)


class RunArtifactsResponse(BaseModel):
    """List of artifact metadata tied to a run."""

    run_id: str
    artifact_paths: list[str] = Field(default_factory=list)
    artifact_refs: dict[str, str] = Field(default_factory=dict)
    report_artifact: ArtifactReference | None = None
    artifact_summary: dict[str, int] = Field(default_factory=dict)

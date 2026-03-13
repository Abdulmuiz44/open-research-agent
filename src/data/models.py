"""Core typed data models for pipeline artifacts and run objects."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    """Input request for a bounded research run."""

    objective: str
    constraints: list[str] = Field(default_factory=list)
    sub_questions: list[str] = Field(default_factory=list)


class ResearchPlan(BaseModel):
    """Planner output containing queries and execution bounds."""

    run_id: str
    search_queries: list[str] = Field(default_factory=list)
    source_budget: int = 10
    stop_conditions: list[str] = Field(default_factory=list)


class CandidateSource(BaseModel):
    """Candidate source discovered via search or crawl."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    url: str
    domain: str | None = None
    query: str | None = None
    rank: int | None = None


class FetchedDocument(BaseModel):
    """Fetched webpage artifact with transport metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    source_id: str
    final_url: str
    status_code: int | None = None
    html: str | None = None
    error: str | None = None


class Source(BaseModel):
    """Normalized source record used in citations."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    url: str
    title: str | None = None
    author: str | None = None
    published_at: datetime | None = None


class ExtractedDocument(BaseModel):
    """Normalized extracted document text and metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    source_id: str
    title: str | None = None
    content: str
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExtractedTable(BaseModel):
    """Structured table extracted from web or local data sources."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    source_id: str | None = None
    name: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)


class AnalysisArtifact(BaseModel):
    """Intermediate or final analysis output tied to evidence."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    kind: str
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)


class Report(BaseModel):
    """Final report object for markdown and JSON outputs."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    objective: str
    findings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ResearchRun(BaseModel):
    """Top-level run metadata and lifecycle state."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    objective: str
    status: str = "created"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

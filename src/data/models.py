"""Core typed data models for pipeline artifacts and run objects."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


class RunStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ArtifactKind(str, Enum):
    SUMMARY = "summary"
    FINDINGS = "findings"
    THEMES = "themes"
    CONTRADICTIONS = "contradictions"
    REPORT_DRAFT = "report_draft"


class ResearchRequest(BaseModel):
    """Input payload for a bounded research run."""

    objective: str = Field(min_length=3)
    constraints: list[str] = Field(default_factory=list)
    max_sources: int = Field(default=10, ge=1, le=100)


class ResearchPlan(BaseModel):
    """Deterministic plan created from a request."""

    objective: str
    research_objectives: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    source_budget: int = Field(default=10, ge=1, le=100)


class ResearchRun(BaseModel):
    """Top-level run metadata and lifecycle state."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    objective: str = Field(min_length=3)
    status: RunStatus = RunStatus.CREATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error_message: str | None = None


class CandidateSource(BaseModel):
    """Source candidate discovered by a search provider."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    query: str
    url: HttpUrl
    domain: str
    title: str | None = None
    snippet: str | None = None
    provider: str
    provider_rank: int = Field(default=0, ge=0)
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class FetchedDocument(BaseModel):
    """HTTP/browser fetch result for a candidate source."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    source_id: str
    requested_url: HttpUrl
    final_url: HttpUrl | None = None
    status_code: int | None = None
    content_type: str | None = None
    content_length: int | None = None
    text: str | None = None
    raw_html: str | None = None
    fetch_method: str = "http"
    success: bool = False
    error: str | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Source(BaseModel):
    """Normalized source record used in citations."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    url: HttpUrl
    domain: str | None = None
    title: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExtractedDocument(BaseModel):
    """Normalized extracted document text and metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    source_id: str
    title: str | None = None
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    content_hash: str | None = None
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExtractedTable(BaseModel):
    """Structured table metadata extracted from sources or local files."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    source_id: str | None = None
    name: str | None = None
    row_count: int = 0
    column_names: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Finding(BaseModel):
    """Deterministic finding tied to one or more sources and snippets."""

    id: str
    title: str
    summary: str
    theme: str | None = None
    supporting_source_ids: list[str] = Field(default_factory=list)
    supporting_source_urls: list[str] = Field(default_factory=list)
    supporting_snippets: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Theme(BaseModel):
    """Recurring theme detected across extracted documents."""

    id: str
    label: str
    key_terms: list[str] = Field(default_factory=list)
    finding_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class Contradiction(BaseModel):
    """Conservative conflict marker where sources disagree on a numeric claim."""

    id: str
    topic: str
    summary: str
    source_ids: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    snippets: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AnalysisSummary(BaseModel):
    """Run-level deterministic analysis overview."""

    total_documents: int = 0
    total_findings: int = 0
    total_themes: int = 0
    total_contradictions: int = 0
    summary: str = ""
    limitations: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Structured result from deterministic analysis stage."""

    findings: list[Finding] = Field(default_factory=list)
    themes: list[Theme] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    summary: AnalysisSummary = Field(default_factory=AnalysisSummary)


class AnalysisArtifact(BaseModel):
    """Intermediate or final analysis output tied to evidence."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    kind: ArtifactKind = ArtifactKind.SUMMARY
    summary: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Report(BaseModel):
    """Simple deterministic report payload."""

    run_id: str
    objective: str
    findings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    markdown: str

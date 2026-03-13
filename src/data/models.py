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
    REPORT_DRAFT = "report_draft"


class ResearchRun(BaseModel):
    """Top-level run metadata and lifecycle state."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    objective: str = Field(min_length=3)
    status: RunStatus = RunStatus.CREATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error_message: str | None = None


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


class AnalysisArtifact(BaseModel):
    """Intermediate or final analysis output tied to evidence."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    kind: ArtifactKind = ArtifactKind.SUMMARY
    summary: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

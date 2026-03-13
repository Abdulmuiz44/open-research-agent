"""Storage interfaces for runs and artifact persistence."""

from __future__ import annotations

from typing import Protocol

from src.data.models import AnalysisArtifact, ExtractedDocument, ResearchRun, Source


class RunStorage(Protocol):
    """Persistence interface for run lifecycle records."""

    def create_run(self, run: ResearchRun) -> ResearchRun:
        """Persist a new run record."""

    def get_run(self, run_id: str) -> ResearchRun | None:
        """Load a run by ID."""


class ArtifactStorage(Protocol):
    """Persistence interface for source, extract, and analysis artifacts."""

    def save_source(self, source: Source) -> None:
        """Persist normalized source artifact."""

    def save_document(self, document: ExtractedDocument) -> None:
        """Persist extracted document artifact."""

    def save_analysis(self, artifact: AnalysisArtifact) -> None:
        """Persist analysis artifact."""

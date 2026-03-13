"""Storage interfaces for run and artifact persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict

from src.data.models import AnalysisArtifact, ExtractedDocument, ExtractedTable, ResearchRun, RunStatus, Source


class StorageBackend(ABC):
    """Abstract storage contract for run lifecycle and artifact metadata."""

    @abstractmethod
    def create_run(self, run: ResearchRun) -> ResearchRun:
        """Persist a new run record."""

    @abstractmethod
    def update_run_status(self, run_id: str, status: RunStatus, *, error_message: str | None = None) -> ResearchRun:
        """Update run status metadata."""

    @abstractmethod
    def save_source(self, source: Source) -> Source:
        """Persist source metadata for a run."""

    @abstractmethod
    def save_extracted_document(self, document: ExtractedDocument) -> ExtractedDocument:
        """Persist extracted document metadata for a run."""

    @abstractmethod
    def save_extracted_table_metadata(self, table: ExtractedTable) -> ExtractedTable:
        """Persist extracted table metadata for a run."""

    @abstractmethod
    def save_analysis_artifact_metadata(self, artifact: AnalysisArtifact) -> AnalysisArtifact:
        """Persist analysis artifact metadata for a run."""

    @abstractmethod
    def get_run(self, run_id: str) -> ResearchRun | None:
        """Load run metadata by run ID."""

    @abstractmethod
    def list_run_artifacts(self, run_id: str) -> list[str]:
        """List artifact IDs associated with a run."""


class LocalStorageStub(StorageBackend):
    """Minimal in-memory storage stub for local runtime and tests."""

    def __init__(self) -> None:
        self._runs: dict[str, ResearchRun] = {}
        self._artifacts: defaultdict[str, list[str]] = defaultdict(list)

    def create_run(self, run: ResearchRun) -> ResearchRun:
        self._runs[run.id] = run
        return run

    def update_run_status(self, run_id: str, status: RunStatus, *, error_message: str | None = None) -> ResearchRun:
        run = self._runs[run_id]
        run.status = status
        run.error_message = error_message
        self._runs[run_id] = run
        return run

    def save_source(self, source: Source) -> Source:
        self._artifacts[source.run_id].append(source.id)
        return source

    def save_extracted_document(self, document: ExtractedDocument) -> ExtractedDocument:
        self._artifacts[document.run_id].append(document.id)
        return document

    def save_extracted_table_metadata(self, table: ExtractedTable) -> ExtractedTable:
        self._artifacts[table.run_id].append(table.id)
        return table

    def save_analysis_artifact_metadata(self, artifact: AnalysisArtifact) -> AnalysisArtifact:
        self._artifacts[artifact.run_id].append(artifact.id)
        return artifact

    def get_run(self, run_id: str) -> ResearchRun | None:
        return self._runs.get(run_id)

    def list_run_artifacts(self, run_id: str) -> list[str]:
        return list(self._artifacts[run_id])

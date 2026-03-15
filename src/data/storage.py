"""Storage interfaces and concrete backends for run/artifact persistence."""

from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.data.models import (
    AnalysisArtifact,
    ExtractedDocument,
    ExtractedTable,
    FetchedDocument,
    ResearchRun,
    RunStatus,
    Source,
)


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
    def save_fetched_document_metadata(self, document: FetchedDocument) -> FetchedDocument:
        """Persist fetched document metadata for a run."""

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
    def save_artifact_json(self, run_id: str, relative_path: str, payload: dict[str, Any] | list[Any]) -> str:
        """Persist a JSON artifact and return absolute path."""

    @abstractmethod
    def save_artifact_markdown(self, run_id: str, relative_path: str, markdown: str) -> str:
        """Persist a markdown artifact and return absolute path."""

    @abstractmethod
    def get_run(self, run_id: str) -> ResearchRun | None:
        """Load run metadata by run ID."""

    @abstractmethod
    def list_run_artifacts(self, run_id: str) -> list[str]:
        """List artifact paths associated with a run."""

    @abstractmethod
    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        """Retrieve key artifact references for a run."""


class SQLiteStorageBackend(StorageBackend):
    """SQLite-backed metadata store with file-based artifacts under runs/<run_id>/."""

    def __init__(self, *, base_dir: Path | None = None, db_path: Path | None = None) -> None:
        settings = get_settings()
        self.base_dir = (base_dir or settings.runs_dir).resolve()
        self.db_path = (db_path or settings.storage_db_path).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def create_run(self, run: ResearchRun) -> ResearchRun:
        self._run_dir(run.id).mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (id, objective, status, created_at, updated_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.objective,
                    run.status.value,
                    run.created_at.isoformat(),
                    run.updated_at.isoformat(),
                    run.error_message,
                ),
            )
        return run

    def update_run_status(self, run_id: str, status: RunStatus, *, error_message: str | None = None) -> ResearchRun:
        now = datetime.now(UTC)
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET status = ?, updated_at = ?, error_message = ? WHERE id = ?",
                (status.value, now.isoformat(), error_message, run_id),
            )

        run = self.get_run(run_id)
        if run is None:
            raise KeyError(f"Run {run_id} not found")
        return run

    def save_source(self, source: Source) -> Source:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sources (
                    id, run_id, url, domain, title, author, published_at, discovered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.id,
                    source.run_id,
                    str(source.url),
                    source.domain,
                    source.title,
                    source.author,
                    source.published_at.isoformat() if source.published_at else None,
                    source.discovered_at.isoformat(),
                ),
            )
        return source

    def save_fetched_document_metadata(self, document: FetchedDocument) -> FetchedDocument:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO fetched_documents (
                    id, run_id, source_id, requested_url, final_url, status_code,
                    content_type, content_length, fetch_method, success, error, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.run_id,
                    document.source_id,
                    str(document.requested_url),
                    str(document.final_url) if document.final_url else None,
                    document.status_code,
                    document.content_type,
                    document.content_length,
                    document.fetch_method,
                    int(document.success),
                    document.error,
                    document.fetched_at.isoformat(),
                ),
            )
        return document

    def save_extracted_document(self, document: ExtractedDocument) -> ExtractedDocument:
        artifact_path = self.save_artifact_json(
            document.run_id,
            f"extracted/{document.source_id}.json",
            document.model_dump(mode="json"),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO extracted_documents (
                    id, run_id, source_id, source_url, final_url, domain, title,
                    extraction_status, content_hash, metadata_json, extracted_at,
                    artifact_relative_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.run_id,
                    document.source_id,
                    str(document.source_url),
                    str(document.final_url) if document.final_url else None,
                    document.domain,
                    document.title,
                    document.extraction_status.value,
                    document.content_hash,
                    json.dumps(document.metadata, sort_keys=True),
                    document.extracted_at.isoformat(),
                    self._relative_from_run_dir(document.run_id, artifact_path),
                ),
            )
        self._upsert_artifact_metadata(document.run_id, f"extracted_{document.source_id}", artifact_path, kind="extracted_document")
        return document

    def save_extracted_table_metadata(self, table: ExtractedTable) -> ExtractedTable:
        relative_path = f"analysis/table_{table.id}.json"
        self.save_artifact_json(table.run_id, relative_path, table.model_dump(mode="json"))
        return table

    def save_analysis_artifact_metadata(self, artifact: AnalysisArtifact) -> AnalysisArtifact:
        artifact_path = self.save_artifact_json(
            artifact.run_id,
            f"analysis/{artifact.kind.value}_{artifact.id}.json",
            artifact.model_dump(mode="json"),
        )
        self._upsert_artifact_metadata(
            artifact.run_id,
            f"analysis_{artifact.id}",
            artifact_path,
            kind=artifact.kind.value,
            metadata={"evidence_ids": artifact.evidence_ids, "summary": artifact.summary},
        )
        return artifact

    def save_artifact_json(self, run_id: str, relative_path: str, payload: dict[str, Any] | list[Any]) -> str:
        path = self._run_dir(run_id) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        kind = self._infer_artifact_kind(relative_path)
        self._upsert_artifact_metadata(run_id, relative_path, str(path), kind=kind)
        return str(path)

    def save_artifact_markdown(self, run_id: str, relative_path: str, markdown: str) -> str:
        path = self._run_dir(run_id) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        kind = self._infer_artifact_kind(relative_path)
        self._upsert_artifact_metadata(run_id, relative_path, str(path), kind=kind)
        return str(path)

    def get_run(self, run_id: str) -> ResearchRun | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, objective, status, created_at, updated_at, error_message FROM runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return ResearchRun(
            id=row["id"],
            objective=row["objective"],
            status=RunStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            error_message=row["error_message"],
        )

    def list_run_artifacts(self, run_id: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT artifact_relative_path FROM artifacts WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
        return [str(row["artifact_relative_path"]) for row in rows]

    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT artifact_key, artifact_absolute_path FROM artifacts WHERE run_id = ?",
                (run_id,),
            ).fetchall()
        return {str(row["artifact_key"]): str(row["artifact_absolute_path"]) for row in rows}

    def _upsert_artifact_metadata(
        self,
        run_id: str,
        artifact_key: str,
        artifact_absolute_path: str,
        *,
        kind: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        relative_path = self._relative_from_run_dir(run_id, artifact_absolute_path)
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO artifacts (
                    run_id, artifact_key, kind, artifact_relative_path, artifact_absolute_path,
                    metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id, artifact_key)
                DO UPDATE SET
                    kind = excluded.kind,
                    artifact_relative_path = excluded.artifact_relative_path,
                    artifact_absolute_path = excluded.artifact_absolute_path,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    run_id,
                    artifact_key,
                    kind,
                    relative_path,
                    str(Path(artifact_absolute_path).resolve()),
                    json.dumps(metadata or {}, sort_keys=True),
                    now,
                    now,
                ),
            )

    def _relative_from_run_dir(self, run_id: str, artifact_absolute_path: str) -> str:
        return str(Path(artifact_absolute_path).resolve().relative_to(self._run_dir(run_id)))

    def _run_dir(self, run_id: str) -> Path:
        return self.base_dir / run_id

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error_message TEXT
                );

                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    domain TEXT,
                    title TEXT,
                    author TEXT,
                    published_at TEXT,
                    discovered_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );

                CREATE TABLE IF NOT EXISTS fetched_documents (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    requested_url TEXT NOT NULL,
                    final_url TEXT,
                    status_code INTEGER,
                    content_type TEXT,
                    content_length INTEGER,
                    fetch_method TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    error TEXT,
                    fetched_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );

                CREATE TABLE IF NOT EXISTS extracted_documents (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    final_url TEXT,
                    domain TEXT,
                    title TEXT,
                    extraction_status TEXT NOT NULL,
                    content_hash TEXT,
                    metadata_json TEXT NOT NULL,
                    extracted_at TEXT NOT NULL,
                    artifact_relative_path TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );

                CREATE TABLE IF NOT EXISTS artifacts (
                    run_id TEXT NOT NULL,
                    artifact_key TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    artifact_relative_path TEXT NOT NULL,
                    artifact_absolute_path TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (run_id, artifact_key),
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_sources_run_id ON sources(run_id);
                CREATE INDEX IF NOT EXISTS idx_fetched_documents_run_id ON fetched_documents(run_id);
                CREATE INDEX IF NOT EXISTS idx_extracted_documents_run_id ON extracted_documents(run_id);
                CREATE INDEX IF NOT EXISTS idx_artifacts_run_id ON artifacts(run_id);
                """
            )

    def _infer_artifact_kind(self, relative_path: str) -> str:
        filename = Path(relative_path).name.lower()
        if filename == "plan.json":
            return "plan"
        if filename.endswith(".md") and "report" in relative_path.lower():
            return "report"
        if filename.startswith("final_result"):
            return "analysis"
        if relative_path.startswith("analysis/"):
            return "analysis"
        if relative_path.startswith("fetched/"):
            return "fetched"
        if relative_path.startswith("extracted/"):
            return "extracted"
        if relative_path.startswith("sources"):
            return "sources"
        if filename == "manifest.json":
            return "manifest"
        return "artifact"


class LocalStorageStub(SQLiteStorageBackend):
    """Backward-compatible alias now backed by SQLite metadata + local files."""


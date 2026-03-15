"""Storage interfaces for run and artifact persistence."""

from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.core.exceptions import StorageError
from src.data.models import (
    AnalysisArtifact,
    ExtractedDocument,
    ExtractedTable,
    FetchedDocument,
    ResearchPlan,
    ResearchRun,
    RunStatus,
    Source,
)


def _artifact_ref_key(relative_path: str) -> str | None:
    if relative_path == "plan.json":
        return "plan"
    if relative_path == "sources.json":
        return "sources"
    if relative_path == "fetched/documents.json":
        return "fetched"
    if relative_path == "extracted/documents.json":
        return "extracted"
    if relative_path == "report/report.md":
        return "report"
    if relative_path == "analysis/final_result.json":
        return "final_result"
    if relative_path.startswith("analysis/") and relative_path.endswith(".json"):
        stem = Path(relative_path).stem
        return f"analysis_{stem.split('_', 1)[-1]}"
    if relative_path.startswith("fetched/") and relative_path.endswith(".json"):
        return f"fetched_{Path(relative_path).stem}"
    if relative_path.startswith("extracted/") and relative_path.endswith(".json"):
        return f"extracted_{Path(relative_path).stem}"
    return None


class StorageBackend(ABC):
    """Abstract storage contract for run lifecycle and artifact metadata."""

    @abstractmethod
    def create_run(self, run: ResearchRun) -> ResearchRun:
        """Persist a new run record."""

    @abstractmethod
    def update_run_status(self, run_id: str, status: RunStatus, *, error_message: str | None = None) -> ResearchRun:
        """Update run status metadata."""

    @abstractmethod
    def save_plan_artifact(self, run_id: str, plan: ResearchPlan) -> str:
        """Persist structured planning artifact for a run and return absolute path."""

    @abstractmethod
    def save_source_metadata(self, source: Source) -> Source:
        """Persist source metadata for a run."""

    def save_source(self, source: Source) -> Source:
        """Compatibility alias for older callers."""
        return self.save_source_metadata(source)

    @abstractmethod
    def save_fetched_metadata(self, fetched: FetchedDocument) -> FetchedDocument:
        """Persist fetched document metadata for a run."""

    @abstractmethod
    def save_extracted_document_metadata(self, document: ExtractedDocument) -> ExtractedDocument:
        """Persist extracted document metadata for a run."""

    def save_extracted_document(self, document: ExtractedDocument) -> ExtractedDocument:
        """Compatibility alias for older callers."""
        return self.save_extracted_document_metadata(document)

    @abstractmethod
    def save_extracted_table_metadata(self, table: ExtractedTable) -> ExtractedTable:
        """Persist extracted table metadata for a run."""

    @abstractmethod
    def save_analysis_artifact_metadata(self, artifact: AnalysisArtifact) -> AnalysisArtifact:
        """Persist analysis artifact metadata for a run."""

    @abstractmethod
    def save_report_artifact_metadata(self, run_id: str, report_path: str) -> str:
        """Persist report artifact metadata and return report path."""

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
    def get_run_sources(self, run_id: str) -> list[Source]:
        """Load source metadata records by run ID."""

    @abstractmethod
    def get_run_artifacts(self, run_id: str) -> list[str]:
        """List artifact paths associated with a run."""

    def list_run_artifacts(self, run_id: str) -> list[str]:
        """Compatibility alias for callers that expect list_* naming."""
        return self.get_run_artifacts(run_id)

    @abstractmethod
    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        """Retrieve key artifact references for a run."""

    @abstractmethod
    def list_runs(self, *, limit: int = 50, offset: int = 0) -> list[ResearchRun]:
        """List run metadata with simple bounded pagination."""


class LocalStorageStub(StorageBackend):
    """Local file-backed storage with in-memory run index for MVP inspection."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or get_settings().runs_dir).resolve()
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(f"Failed to initialize runs directory at {self.base_dir}: {exc}") from exc
        self._runs: dict[str, ResearchRun] = {}
        self._sources: defaultdict[str, list[Source]] = defaultdict(list)
        self._artifacts: defaultdict[str, list[str]] = defaultdict(list)

    def create_run(self, run: ResearchRun) -> ResearchRun:
        self._runs[run.id] = run
        try:
            self._run_dir(run.id).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(f"Failed to create run directory for {run.id}: {exc}") from exc
        return run

    def update_run_status(self, run_id: str, status: RunStatus, *, error_message: str | None = None) -> ResearchRun:
        run = self._runs[run_id]
        run.status = status
        run.error_message = error_message
        run.updated_at = datetime.now(UTC)
        self._runs[run_id] = run
        return run

    def save_plan_artifact(self, run_id: str, plan: ResearchPlan) -> str:
        return self.save_artifact_json(run_id, "plan.json", plan.model_dump(mode="json"))

    def save_source_metadata(self, source: Source) -> Source:
        self._sources[source.run_id].append(source)
        self.save_artifact_json(source.run_id, f"sources/{source.id}.json", source.model_dump(mode="json"))
        return source

    def save_fetched_metadata(self, fetched: FetchedDocument) -> FetchedDocument:
        self.save_artifact_json(fetched.run_id, f"fetched/{fetched.source_id}.json", fetched.model_dump(mode="json"))
        return fetched

    def save_extracted_document_metadata(self, document: ExtractedDocument) -> ExtractedDocument:
        self.save_artifact_json(document.run_id, f"extracted/{document.source_id}.json", document.model_dump(mode="json"))
        return document

    def save_extracted_table_metadata(self, table: ExtractedTable) -> ExtractedTable:
        self._track(table.run_id, f"analysis/table_{table.id}.json")
        return table

    def save_analysis_artifact_metadata(self, artifact: AnalysisArtifact) -> AnalysisArtifact:
        self.save_artifact_json(artifact.run_id, f"analysis/{artifact.kind.value}_{artifact.id}.json", artifact.model_dump(mode="json"))
        return artifact

    def save_report_artifact_metadata(self, run_id: str, report_path: str) -> str:
        relative_path = self._relative_artifact_path(run_id, report_path)
        self._track(run_id, relative_path)
        return report_path

    def save_artifact_json(self, run_id: str, relative_path: str, payload: dict[str, Any] | list[Any]) -> str:
        path = self._run_dir(run_id) / relative_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to write JSON artifact {relative_path} for run {run_id}: {exc}") from exc
        self._track(run_id, relative_path)
        return str(path)

    def save_artifact_markdown(self, run_id: str, relative_path: str, markdown: str) -> str:
        path = self._run_dir(run_id) / relative_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(markdown, encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to write markdown artifact {relative_path} for run {run_id}: {exc}") from exc
        self._track(run_id, relative_path)
        return str(path)

    def get_run(self, run_id: str) -> ResearchRun | None:
        return self._runs.get(run_id)

    def get_run_sources(self, run_id: str) -> list[Source]:
        return list(self._sources[run_id])

    def get_run_artifacts(self, run_id: str) -> list[str]:
        return list(self._artifacts[run_id])

    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        refs: dict[str, str] = {}
        for relative_path in self._artifacts[run_id]:
            key = _artifact_ref_key(relative_path)
            if key is not None:
                refs[key] = str((self._run_dir(run_id) / relative_path).resolve())
        return refs

    def list_runs(self, *, limit: int = 50, offset: int = 0) -> list[ResearchRun]:
        if limit <= 0:
            return []
        runs = sorted(self._runs.values(), key=lambda item: item.created_at, reverse=True)
        return runs[max(0, offset) : max(0, offset) + limit]

    def _track(self, run_id: str, relative_path: str) -> None:
        if relative_path not in self._artifacts[run_id]:
            self._artifacts[run_id].append(relative_path)

    def _run_dir(self, run_id: str) -> Path:
        return self.base_dir / run_id

    def _relative_artifact_path(self, run_id: str, artifact_path: str) -> str:
        path = Path(artifact_path)
        try:
            return path.resolve().relative_to(self._run_dir(run_id).resolve()).as_posix()
        except ValueError:
            return path.as_posix()


class SQLiteStorageBackend(StorageBackend):
    """SQLite-backed storage for run metadata and artifact tracking."""

    def __init__(self, db_path: Path | None = None, base_dir: Path | None = None) -> None:
        settings = get_settings()
        self.base_dir = (base_dir or settings.runs_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = (db_path or self.base_dir / "runs.sqlite3").resolve()
        self._initialize_schema()

    def create_run(self, run: ResearchRun) -> ResearchRun:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO runs (id, objective, status, created_at, updated_at, error_message) VALUES (?, ?, ?, ?, ?, ?)",
                (run.id, run.objective, run.status.value, run.created_at.isoformat(), run.updated_at.isoformat(), run.error_message),
            )
        self._run_dir(run.id).mkdir(parents=True, exist_ok=True)
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
            msg = f"Run {run_id} not found"
            raise KeyError(msg)
        return run

    def save_plan_artifact(self, run_id: str, plan: ResearchPlan) -> str:
        return self.save_artifact_json(run_id, "plan.json", plan.model_dump(mode="json"))

    def save_source_metadata(self, source: Source) -> Source:
        payload = source.model_dump(mode="json")
        self.save_artifact_json(source.run_id, f"sources/{source.id}.json", payload)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sources (id, run_id, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (source.id, source.run_id, json.dumps(payload), source.discovered_at.isoformat()),
            )
        return source

    def save_fetched_metadata(self, fetched: FetchedDocument) -> FetchedDocument:
        payload = fetched.model_dump(mode="json")
        self.save_artifact_json(fetched.run_id, f"fetched/{fetched.source_id}.json", payload)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO fetched_documents (id, run_id, source_id, payload_json, fetched_at) VALUES (?, ?, ?, ?, ?)",
                (fetched.id, fetched.run_id, fetched.source_id, json.dumps(payload), fetched.fetched_at.isoformat()),
            )
        return fetched

    def save_extracted_document_metadata(self, document: ExtractedDocument) -> ExtractedDocument:
        payload = document.model_dump(mode="json")
        self.save_artifact_json(document.run_id, f"extracted/{document.source_id}.json", payload)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO extracted_documents (id, run_id, source_id, payload_json, extracted_at) VALUES (?, ?, ?, ?, ?)",
                (document.id, document.run_id, document.source_id, json.dumps(payload), document.extracted_at.isoformat()),
            )
        return document

    def save_extracted_table_metadata(self, table: ExtractedTable) -> ExtractedTable:
        self._track(table.run_id, f"analysis/table_{table.id}.json")
        return table

    def save_analysis_artifact_metadata(self, artifact: AnalysisArtifact) -> AnalysisArtifact:
        payload = artifact.model_dump(mode="json")
        self.save_artifact_json(artifact.run_id, f"analysis/{artifact.kind.value}_{artifact.id}.json", payload)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO analysis_artifacts (id, run_id, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (artifact.id, artifact.run_id, json.dumps(payload), artifact.created_at.isoformat()),
            )
        return artifact

    def save_report_artifact_metadata(self, run_id: str, report_path: str) -> str:
        self._track(run_id, self._relative_artifact_path(run_id, report_path))
        return report_path

    def save_artifact_json(self, run_id: str, relative_path: str, payload: dict[str, Any] | list[Any]) -> str:
        path = self._run_dir(run_id) / relative_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to write JSON artifact {relative_path} for run {run_id}: {exc}") from exc
        self._track(run_id, relative_path)
        return str(path)

    def save_artifact_markdown(self, run_id: str, relative_path: str, markdown: str) -> str:
        path = self._run_dir(run_id) / relative_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(markdown, encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to write markdown artifact {relative_path} for run {run_id}: {exc}") from exc
        self._track(run_id, relative_path)
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

    def get_run_sources(self, run_id: str) -> list[Source]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload_json FROM sources WHERE run_id = ? ORDER BY created_at", (run_id,)).fetchall()
        return [Source.model_validate_json(row[0]) for row in rows]

    def get_run_artifacts(self, run_id: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT relative_path FROM artifacts WHERE run_id = ? ORDER BY created_at, relative_path", (run_id,)).fetchall()
        return [row[0] for row in rows]

    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        refs: dict[str, str] = {}
        for relative_path in self.get_run_artifacts(run_id):
            key = _artifact_ref_key(relative_path)
            if key is not None:
                refs[key] = str((self._run_dir(run_id) / relative_path).resolve())
        return refs

    def list_runs(self, *, limit: int = 50, offset: int = 0) -> list[ResearchRun]:
        bounded_limit = max(0, min(limit, 200))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, objective, status, created_at, updated_at, error_message FROM runs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (bounded_limit, max(0, offset)),
            ).fetchall()
        return [
            ResearchRun(
                id=row["id"],
                objective=row["objective"],
                status=RunStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                error_message=row["error_message"],
            )
            for row in rows
        ]

    def _track(self, run_id: str, relative_path: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO artifacts (run_id, relative_path, created_at) VALUES (?, ?, ?)",
                (run_id, relative_path, datetime.now(UTC).isoformat()),
            )

    def _run_dir(self, run_id: str) -> Path:
        return self.base_dir / run_id

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

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
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS fetched_documents (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    fetched_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS extracted_documents (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    extracted_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS analysis_artifacts (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    run_id TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (run_id, relative_path)
                );
                """
            )

    def _relative_artifact_path(self, run_id: str, artifact_path: str) -> str:
        path = Path(artifact_path)
        try:
            return path.resolve().relative_to(self._run_dir(run_id).resolve()).as_posix()
        except ValueError:
            return path.as_posix()

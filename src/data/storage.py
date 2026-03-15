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
    def save_artifact_json(self, run_id: str, relative_path: str, payload: dict[str, Any] | list[Any]) -> str:
        """Persist a JSON artifact and return absolute path."""

    @abstractmethod
    def save_artifact_markdown(self, run_id: str, relative_path: str, markdown: str) -> str:
        """Persist a markdown artifact and return absolute path."""

    @abstractmethod
    def get_run(self, run_id: str) -> ResearchRun | None:
        """Load run metadata by run ID."""

    @abstractmethod
    def list_runs(self) -> list[ResearchRun]:
        """List all runs in reverse-chronological order."""

    @abstractmethod
    def list_run_artifacts(self, run_id: str) -> list[str]:
        """List artifact paths associated with a run."""

    @abstractmethod
    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        """Retrieve key artifact references for a run."""


class LocalStorageStub(StorageBackend):
    """Local file-backed storage with in-memory run index for MVP inspection."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or get_settings().runs_dir).resolve()
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(f"Failed to initialize runs directory at {self.base_dir}: {exc}") from exc
        self._runs: dict[str, ResearchRun] = {}
        self._artifacts: defaultdict[str, list[str]] = defaultdict(list)
        self._artifact_refs: defaultdict[str, dict[str, str]] = defaultdict(dict)

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

    def save_source(self, source: Source) -> Source:
        self._track(source.run_id, f"sources/{source.id}.json")
        return source

    def save_extracted_document(self, document: ExtractedDocument) -> ExtractedDocument:
        path = self.save_artifact_json(document.run_id, f"extracted/{document.source_id}.json", document.model_dump(mode="json"))
        self._artifact_refs[document.run_id][f"extracted_{document.source_id}"] = path
        return document

    def save_extracted_table_metadata(self, table: ExtractedTable) -> ExtractedTable:
        self._track(table.run_id, f"analysis/table_{table.id}.json")
        return table

    def save_analysis_artifact_metadata(self, artifact: AnalysisArtifact) -> AnalysisArtifact:
        path = self.save_artifact_json(artifact.run_id, f"analysis/{artifact.kind.value}_{artifact.id}.json", artifact.model_dump(mode="json"))
        self._artifact_refs[artifact.run_id][f"analysis_{artifact.id}"] = path
        return artifact

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

    def list_runs(self) -> list[ResearchRun]:
        return sorted(self._runs.values(), key=lambda run: run.created_at, reverse=True)

    def list_run_artifacts(self, run_id: str) -> list[str]:
        return list(self._artifacts[run_id])

    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        return dict(self._artifact_refs[run_id])

    def _track(self, run_id: str, relative_path: str) -> None:
        if relative_path not in self._artifacts[run_id]:
            self._artifacts[run_id].append(relative_path)

    def _run_dir(self, run_id: str) -> Path:
        return self.base_dir / run_id


class SQLiteStorageBackend(StorageBackend):
    """SQLite-backed run index with filesystem artifacts for persistence across process restarts."""

    def __init__(self, db_path: Path, base_dir: Path | None = None) -> None:
        self.db_path = db_path.resolve()
        self.base_dir = (base_dir or get_settings().runs_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def create_run(self, run: ResearchRun) -> ResearchRun:
        with sqlite3.connect(self.db_path) as conn:
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
        self._run_dir(run.id).mkdir(parents=True, exist_ok=True)
        return run

    def update_run_status(self, run_id: str, status: RunStatus, *, error_message: str | None = None) -> ResearchRun:
        run = self.get_run(run_id)
        if run is None:
            raise KeyError(run_id)
        run.status = status
        run.error_message = error_message
        run.updated_at = datetime.now(UTC)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE runs
                SET status = ?, updated_at = ?, error_message = ?
                WHERE id = ?
                """,
                (run.status.value, run.updated_at.isoformat(), run.error_message, run.id),
            )
        return run

    def save_source(self, source: Source) -> Source:
        self._track(source.run_id, f"sources/{source.id}.json")
        return source

    def save_extracted_document(self, document: ExtractedDocument) -> ExtractedDocument:
        path = self.save_artifact_json(document.run_id, f"extracted/{document.source_id}.json", document.model_dump(mode="json"))
        self._save_ref(document.run_id, f"extracted_{document.source_id}", path)
        return document

    def save_extracted_table_metadata(self, table: ExtractedTable) -> ExtractedTable:
        self._track(table.run_id, f"analysis/table_{table.id}.json")
        return table

    def save_analysis_artifact_metadata(self, artifact: AnalysisArtifact) -> AnalysisArtifact:
        path = self.save_artifact_json(artifact.run_id, f"analysis/{artifact.kind.value}_{artifact.id}.json", artifact.model_dump(mode="json"))
        self._save_ref(artifact.run_id, f"analysis_{artifact.id}", path)
        return artifact

    def save_artifact_json(self, run_id: str, relative_path: str, payload: dict[str, Any] | list[Any]) -> str:
        path = self._run_dir(run_id) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        self._track(run_id, relative_path)
        return str(path)

    def save_artifact_markdown(self, run_id: str, relative_path: str, markdown: str) -> str:
        path = self._run_dir(run_id) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        self._track(run_id, relative_path)
        return str(path)

    def get_run(self, run_id: str) -> ResearchRun | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id, objective, status, created_at, updated_at, error_message FROM runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return ResearchRun(
            id=row[0],
            objective=row[1],
            status=RunStatus(row[2]),
            created_at=datetime.fromisoformat(row[3]),
            updated_at=datetime.fromisoformat(row[4]),
            error_message=row[5],
        )

    def list_run_artifacts(self, run_id: str) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT relative_path FROM artifacts WHERE run_id = ? ORDER BY relative_path",
                (run_id,),
            ).fetchall()
        return [row[0] for row in rows]

    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT ref_key, absolute_path FROM artifact_refs WHERE run_id = ? ORDER BY ref_key",
                (run_id,),
            ).fetchall()
        refs = {row[0]: row[1] for row in rows}

        manifest_path = self._run_dir(run_id) / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_paths = manifest.get("paths", {})
            for key, path in manifest_paths.items():
                if isinstance(path, str):
                    refs.setdefault(key, path)

        return refs

    def _track(self, run_id: str, relative_path: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO artifacts (run_id, relative_path) VALUES (?, ?)",
                (run_id, relative_path),
            )

    def _save_ref(self, run_id: str, key: str, absolute_path: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO artifact_refs (run_id, ref_key, absolute_path)
                VALUES (?, ?, ?)
                ON CONFLICT(run_id, ref_key) DO UPDATE SET absolute_path = excluded.absolute_path
                """,
                (run_id, key, absolute_path),
            )

    def _run_dir(self, run_id: str) -> Path:
        return self.base_dir / run_id

    def _initialize(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error_message TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    run_id TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    PRIMARY KEY (run_id, relative_path)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifact_refs (
                    run_id TEXT NOT NULL,
                    ref_key TEXT NOT NULL,
                    absolute_path TEXT NOT NULL,
                    PRIMARY KEY (run_id, ref_key)
                )
                """
            )

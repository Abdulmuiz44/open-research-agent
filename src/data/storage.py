"""Storage interfaces and concrete backends for run/artifact persistence."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
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
        """Persist structured planning artifact for a run and return its absolute path."""

    @abstractmethod
    def save_source_metadata(self, source: Source) -> Source:
        """Persist source metadata for a run."""

    def save_source(self, source: Source) -> Source:
        return self.save_source_metadata(source)

    @abstractmethod
    def save_fetched_metadata(self, fetched: FetchedDocument) -> FetchedDocument:
        """Persist fetched document metadata for a run."""

    def save_fetched_document_metadata(self, fetched: FetchedDocument) -> FetchedDocument:
        return self.save_fetched_metadata(fetched)

    @abstractmethod
    def save_extracted_document_metadata(self, document: ExtractedDocument) -> ExtractedDocument:
        """Persist extracted document metadata for a run."""

    def save_extracted_document(self, document: ExtractedDocument) -> ExtractedDocument:
        return self.save_extracted_document_metadata(document)

    @abstractmethod
    def save_extracted_table_metadata(self, table: ExtractedTable) -> ExtractedTable:
        """Persist extracted table metadata for a run."""

    @abstractmethod
    def save_analysis_artifact_metadata(self, artifact: AnalysisArtifact) -> AnalysisArtifact:
        """Persist analysis artifact metadata for a run."""

    @abstractmethod
    def save_report_artifact_metadata(self, run_id: str, report_path: str) -> str:
        """Persist report artifact metadata and return its path."""

    @abstractmethod
    def save_artifact_json(self, run_id: str, relative_path: str, payload: dict[str, Any] | list[Any]) -> str:
        """Persist a JSON artifact and return its absolute path."""

    @abstractmethod
    def save_artifact_markdown(self, run_id: str, relative_path: str, markdown: str) -> str:
        """Persist a markdown artifact and return its absolute path."""

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
        return self.get_run_artifacts(run_id)

    @abstractmethod
    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        """Retrieve key artifact references for a run."""

    @abstractmethod
    def list_runs(self, *, limit: int = 50, offset: int = 0) -> list[ResearchRun]:
        """List runs in reverse-chronological order."""


class LocalPersistentStorage(StorageBackend):
    """File-backed storage that persists run metadata and artifact indexes."""

    _RUN_METADATA_FILE = "run.json"
    _ARTIFACT_INDEX_FILE = ".artifacts.json"
    _ARTIFACT_REFS_FILE = ".artifact_refs.json"

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or get_settings().runs_dir).resolve()
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(f"Failed to initialize runs directory at {self.base_dir}: {exc}") from exc

    def create_run(self, run: ResearchRun) -> ResearchRun:
        run_dir = self._run_dir(run.id)
        try:
            run_dir.mkdir(parents=True, exist_ok=True)
            self._write_json(run_dir / self._RUN_METADATA_FILE, run.model_dump(mode="json"))
            self._ensure_index_files(run.id)
        except OSError as exc:
            raise StorageError(f"Failed to create run directory for {run.id}: {exc}") from exc
        return run

    def update_run_status(self, run_id: str, status: RunStatus, *, error_message: str | None = None) -> ResearchRun:
        run = self.get_run(run_id)
        if run is None:
            raise KeyError(f"Run {run_id} not found")
        run.status = status
        run.error_message = error_message
        run.updated_at = datetime.now(UTC)
        self._write_json(self._run_dir(run_id) / self._RUN_METADATA_FILE, run.model_dump(mode="json"))
        return run

    def save_plan_artifact(self, run_id: str, plan: ResearchPlan) -> str:
        return self.save_artifact_json(run_id, "plan.json", plan.model_dump(mode="json"))

    def save_source_metadata(self, source: Source) -> Source:
        path = self.save_artifact_json(source.run_id, f"sources/{source.id}.json", source.model_dump(mode="json"))
        refs = self.get_run_artifact_refs(source.run_id)
        refs[f"source_{source.id}"] = path
        self._write_refs(source.run_id, refs)
        return source

    def save_fetched_metadata(self, fetched: FetchedDocument) -> FetchedDocument:
        path = self.save_artifact_json(fetched.run_id, f"fetched/{fetched.source_id}.json", fetched.model_dump(mode="json"))
        refs = self.get_run_artifact_refs(fetched.run_id)
        refs[f"fetched_{fetched.source_id}"] = path
        self._write_refs(fetched.run_id, refs)
        return fetched

    def save_extracted_document_metadata(self, document: ExtractedDocument) -> ExtractedDocument:
        path = self.save_artifact_json(document.run_id, f"extracted/{document.source_id}.json", document.model_dump(mode="json"))
        refs = self.get_run_artifact_refs(document.run_id)
        refs[f"extracted_{document.source_id}"] = path
        self._write_refs(document.run_id, refs)
        return document

    def save_extracted_table_metadata(self, table: ExtractedTable) -> ExtractedTable:
        self.save_artifact_json(table.run_id, f"analysis/table_{table.id}.json", table.model_dump(mode="json"))
        return table

    def save_analysis_artifact_metadata(self, artifact: AnalysisArtifact) -> AnalysisArtifact:
        path = self.save_artifact_json(
            artifact.run_id,
            f"analysis/{artifact.kind.value}_{artifact.id}.json",
            artifact.model_dump(mode="json"),
        )
        refs = self.get_run_artifact_refs(artifact.run_id)
        refs[f"analysis_{artifact.id}"] = path
        self._write_refs(artifact.run_id, refs)
        return artifact

    def save_report_artifact_metadata(self, run_id: str, report_path: str) -> str:
        refs = self.get_run_artifact_refs(run_id)
        refs["report"] = report_path
        self._write_refs(run_id, refs)
        return report_path

    def save_artifact_json(self, run_id: str, relative_path: str, payload: dict[str, Any] | list[Any]) -> str:
        path = self._run_dir(run_id) / relative_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self._write_json(path, payload)
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
        payload = self._read_json(self._run_dir(run_id) / self._RUN_METADATA_FILE)
        if payload is None:
            return None
        return ResearchRun.model_validate(payload)

    def get_run_sources(self, run_id: str) -> list[Source]:
        refs = self.get_run_artifact_refs(run_id)
        sources: list[Source] = []
        for key, path in refs.items():
            if not key.startswith("source_"):
                continue
            payload = self._read_json(Path(path))
            if isinstance(payload, dict):
                sources.append(Source.model_validate(payload))
        return sources

    def get_run_artifacts(self, run_id: str) -> list[str]:
        index = self._read_json(self._run_dir(run_id) / self._ARTIFACT_INDEX_FILE)
        if isinstance(index, list):
            return [item for item in index if isinstance(item, str)]

        run_dir = self._run_dir(run_id)
        if not run_dir.exists():
            return []
        return sorted(
            str(item.relative_to(run_dir)).replace("\\", "/")
            for item in run_dir.rglob("*")
            if item.is_file() and item.name not in {self._RUN_METADATA_FILE, self._ARTIFACT_INDEX_FILE, self._ARTIFACT_REFS_FILE}
        )

    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        merged: dict[str, str] = {}
        refs = self._read_json(self._run_dir(run_id) / self._ARTIFACT_REFS_FILE)
        if isinstance(refs, dict):
            merged.update({str(key): str(value) for key, value in refs.items()})

        manifest = self._read_json(self._run_dir(run_id) / "manifest.json")
        if isinstance(manifest, dict):
            paths = manifest.get("paths")
            if isinstance(paths, dict):
                merged.update({str(key): str(value) for key, value in paths.items()})
        return merged

    def list_runs(self, *, limit: int = 50, offset: int = 0) -> list[ResearchRun]:
        runs: list[ResearchRun] = []
        directories = [path for path in self.base_dir.glob("*") if path.is_dir()]
        directories.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        for run_dir in directories[offset:]:
            run = self.get_run(run_dir.name)
            if run is not None:
                runs.append(run)
            if len(runs) >= limit:
                break
        return runs

    def _track(self, run_id: str, relative_path: str) -> None:
        artifacts = self.get_run_artifacts(run_id)
        normalized = relative_path.replace("\\", "/")
        if normalized not in artifacts:
            artifacts.append(normalized)
            artifacts.sort()
            self._write_json(self._run_dir(run_id) / self._ARTIFACT_INDEX_FILE, artifacts)

    def _run_dir(self, run_id: str) -> Path:
        return self.base_dir / run_id

    def _ensure_index_files(self, run_id: str) -> None:
        run_dir = self._run_dir(run_id)
        if not (run_dir / self._ARTIFACT_INDEX_FILE).exists():
            self._write_json(run_dir / self._ARTIFACT_INDEX_FILE, [])
        if not (run_dir / self._ARTIFACT_REFS_FILE).exists():
            self._write_json(run_dir / self._ARTIFACT_REFS_FILE, {})

    def _write_refs(self, run_id: str, refs: dict[str, str]) -> None:
        self._write_json(self._run_dir(run_id) / self._ARTIFACT_REFS_FILE, refs)

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


LocalStorageStub = LocalPersistentStorage

"""Storage interfaces for run and artifact persistence."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.core.config import get_settings
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
    def list_run_artifacts(self, run_id: str) -> list[str]:
        """List artifact paths associated with a run."""

    @abstractmethod
    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        """Retrieve key artifact references for a run."""


class LocalPersistentStorage(StorageBackend):
    """File-backed storage that persists run metadata and artifact indexes."""

    _RUN_METADATA_FILE = "run.json"
    _ARTIFACT_INDEX_FILE = ".artifacts.json"
    _ARTIFACT_REFS_FILE = ".artifact_refs.json"

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or get_settings().runs_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_run(self, run: ResearchRun) -> ResearchRun:
        run_dir = self._run_dir(run.id)
        run_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(run_dir / self._RUN_METADATA_FILE, run.model_dump(mode="json"))
        self._ensure_index_files(run.id)
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

    def save_source(self, source: Source) -> Source:
        path = self.save_artifact_json(source.run_id, f"sources/{source.id}.json", source.model_dump(mode="json"))
        refs = self.get_run_artifact_refs(source.run_id)
        refs[f"source_{source.id}"] = path
        self._write_refs(source.run_id, refs)
        return source

    def save_extracted_document(self, document: ExtractedDocument) -> ExtractedDocument:
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

    def save_artifact_json(self, run_id: str, relative_path: str, payload: dict[str, Any] | list[Any]) -> str:
        path = self._run_dir(run_id) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write_json(path, payload)
        self._track(run_id, relative_path)
        return str(path)

    def save_artifact_markdown(self, run_id: str, relative_path: str, markdown: str) -> str:
        path = self._run_dir(run_id) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        self._track(run_id, relative_path)
        return str(path)

    def get_run(self, run_id: str) -> ResearchRun | None:
        path = self._run_dir(run_id) / self._RUN_METADATA_FILE
        payload = self._read_json(path)
        if payload is None:
            return None
        return ResearchRun.model_validate(payload)

    def list_run_artifacts(self, run_id: str) -> list[str]:
        path = self._run_dir(run_id) / self._ARTIFACT_INDEX_FILE
        index = self._read_json(path)
        if isinstance(index, list):
            return [item for item in index if isinstance(item, str)]

        run_dir = self._run_dir(run_id)
        if not run_dir.exists():
            return []
        return sorted(
            str(item.relative_to(run_dir))
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

    def list_runs(self, limit: int = 20) -> list[ResearchRun]:
        runs: list[ResearchRun] = []
        for run_dir in sorted(self.base_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
            if not run_dir.is_dir():
                continue
            run = self.get_run(run_dir.name)
            if run is not None:
                runs.append(run)
            if len(runs) >= limit:
                break
        return runs

    def _track(self, run_id: str, relative_path: str) -> None:
        artifacts = self.list_run_artifacts(run_id)
        if relative_path not in artifacts:
            artifacts.append(relative_path)
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

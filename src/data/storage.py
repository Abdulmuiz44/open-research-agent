"""Storage interfaces for run and artifact persistence."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import defaultdict
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


class LocalStorageStub(StorageBackend):
    """Local file-backed storage with in-memory run index for MVP inspection."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or get_settings().runs_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._runs: dict[str, ResearchRun] = {}
        self._artifacts: defaultdict[str, list[str]] = defaultdict(list)
        self._artifact_refs: defaultdict[str, dict[str, str]] = defaultdict(dict)

    def create_run(self, run: ResearchRun) -> ResearchRun:
        self._runs[run.id] = run
        self._run_dir(run.id).mkdir(parents=True, exist_ok=True)
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
        in_memory = self._runs.get(run_id)
        if in_memory is not None:
            return in_memory

        manifest_path = self._run_dir(run_id) / "manifest.json"
        if not manifest_path.exists():
            return None

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            run = ResearchRun(
                id=manifest.get("run_id", run_id),
                objective=manifest.get("objective", "unknown objective"),
                status=RunStatus(manifest.get("status", RunStatus.CREATED.value)),
                created_at=manifest.get("created_at", datetime.now(UTC).isoformat()),
                updated_at=manifest.get("updated_at", datetime.now(UTC).isoformat()),
            )
            self._runs[run_id] = run
            return run
        except (json.JSONDecodeError, ValueError):
            return None

    def list_run_artifacts(self, run_id: str) -> list[str]:
        in_memory = list(self._artifacts[run_id])
        if in_memory:
            return in_memory

        run_dir = self._run_dir(run_id)
        if not run_dir.exists():
            return []

        discovered_paths = sorted(
            str(path.relative_to(run_dir)) for path in run_dir.rglob("*") if path.is_file()
        )
        self._artifacts[run_id].extend(discovered_paths)
        return discovered_paths

    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        in_memory = dict(self._artifact_refs[run_id])
        if in_memory:
            return in_memory

        manifest_path = self._run_dir(run_id) / "manifest.json"
        if not manifest_path.exists():
            return {}

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

        path_refs = manifest.get("paths", {})
        if not isinstance(path_refs, dict):
            return {}

        self._artifact_refs[run_id].update(
            {
                key: str(value)
                for key, value in path_refs.items()
                if isinstance(key, str) and isinstance(value, str)
            }
        )
        return dict(self._artifact_refs[run_id])

    def _track(self, run_id: str, relative_path: str) -> None:
        if relative_path not in self._artifacts[run_id]:
            self._artifacts[run_id].append(relative_path)

    def _run_dir(self, run_id: str) -> Path:
        return self.base_dir / run_id

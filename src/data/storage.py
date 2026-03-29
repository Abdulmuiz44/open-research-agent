"""Storage interfaces and local persistence for run/artifact state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from src.core.config import get_settings
from src.core.exceptions import StorageError
from src.data.models import AnalysisArtifact, ExtractedDocument, Report, ResearchRun, Source


class RunStorage(Protocol):
    """Persistence interface for run lifecycle records."""

    def create_run(self, run: ResearchRun) -> ResearchRun:
        """Persist a new run record."""

    def get_run(self, run_id: str) -> ResearchRun | None:
        """Load a run by ID."""

    def list_runs(self) -> list[ResearchRun]:
        """Return all known runs in reverse chronological order."""


class ArtifactStorage(Protocol):
    """Persistence interface for source, extract, and analysis artifacts."""

    def save_source(self, source: Source) -> None:
        """Persist normalized source artifact."""

    def save_document(self, document: ExtractedDocument) -> None:
        """Persist extracted document artifact."""

    def save_analysis(self, artifact: AnalysisArtifact) -> None:
        """Persist analysis artifact."""


class LocalStorage:
    """Filesystem-backed storage for runs and artifact references."""

    def __init__(self, runs_dir: Path | None = None) -> None:
        self.runs_dir = (runs_dir or get_settings().runs_dir).resolve()
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def create_run(self, run: ResearchRun) -> ResearchRun:
        run_dir = self._run_dir(run.id)
        run_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(run_dir / "run.json", run.model_dump(mode="json"))
        self._write_json(run_dir / ".artifacts.json", [])
        self._write_json(run_dir / ".artifact_refs.json", {})
        return run

    def update_run(self, run: ResearchRun) -> ResearchRun:
        self._write_json(self._run_dir(run.id) / "run.json", run.model_dump(mode="json"))
        return run

    def get_run(self, run_id: str) -> ResearchRun | None:
        payload = self._read_json(self._run_dir(run_id) / "run.json")
        if payload is None:
            return None
        return ResearchRun.model_validate(payload)

    def list_runs(self) -> list[ResearchRun]:
        runs: list[ResearchRun] = []
        for path in sorted(self.runs_dir.glob("*"), key=lambda item: item.stat().st_mtime, reverse=True):
            if not path.is_dir():
                continue
            run = self.get_run(path.name)
            if run is not None:
                runs.append(run)
        return runs

    def save_source(self, source: Source) -> None:
        path = self.save_artifact_json(source.run_id, f"sources/{source.id}.json", source.model_dump(mode="json"))
        self._set_ref(source.run_id, f"source_{source.id}", path)

    def save_document(self, document: ExtractedDocument) -> None:
        path = self.save_artifact_json(document.run_id, f"extracted/{document.id}.json", document.model_dump(mode="json"))
        self._set_ref(document.run_id, f"document_{document.id}", path)

    def save_analysis(self, artifact: AnalysisArtifact) -> None:
        path = self.save_artifact_json(artifact.run_id, f"analysis/{artifact.id}.json", artifact.model_dump(mode="json"))
        self._set_ref(artifact.run_id, f"analysis_{artifact.id}", path)

    def save_report(self, report: Report, markdown: str) -> str:
        path = self.save_artifact_text(report.run_id, "report/report.md", markdown)
        self._set_ref(report.run_id, "report", path)
        return path

    def save_artifact_json(self, run_id: str, relative_path: str, payload: dict[str, Any] | list[Any]) -> str:
        path = self._run_dir(run_id) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write_json(path, payload)
        self._track(run_id, relative_path)
        return str(path.resolve())

    def save_artifact_text(self, run_id: str, relative_path: str, text: str) -> str:
        path = self._run_dir(run_id) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(text, encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to write artifact {relative_path} for run {run_id}: {exc}") from exc
        self._track(run_id, relative_path)
        return str(path.resolve())

    def list_run_artifacts(self, run_id: str) -> list[str]:
        payload = self._read_json(self._run_dir(run_id) / ".artifacts.json")
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, str)]
        return []

    def get_run_artifact_refs(self, run_id: str) -> dict[str, str]:
        payload = self._read_json(self._run_dir(run_id) / ".artifact_refs.json")
        if isinstance(payload, dict):
            return {str(k): str(v) for k, v in payload.items()}
        return {}

    def _run_dir(self, run_id: str) -> Path:
        return self.runs_dir / run_id

    def _track(self, run_id: str, relative_path: str) -> None:
        artifacts = self.list_run_artifacts(run_id)
        normalized = relative_path.replace("\\", "/")
        if normalized not in artifacts:
            artifacts.append(normalized)
            artifacts.sort()
            self._write_json(self._run_dir(run_id) / ".artifacts.json", artifacts)

    def _set_ref(self, run_id: str, key: str, value: str) -> None:
        refs = self.get_run_artifact_refs(run_id)
        refs[key] = value
        self._write_json(self._run_dir(run_id) / ".artifact_refs.json", refs)

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"Failed to read JSON file {path}: {exc}") from exc

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
        try:
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to write JSON file {path}: {exc}") from exc

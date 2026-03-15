"""Helpers for deterministic run artifact layout and manifest construction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.data.models import RunStatus


@dataclass(frozen=True)
class RunArtifactLayout:
    """Canonical relative paths for run artifacts under outputs/runs/<run_id>/."""

    MANIFEST: str = "manifest.json"
    PLAN: str = "plan.json"
    SOURCES: str = "sources.json"
    FETCHED_DIR: str = "fetched"
    EXTRACTED_DIR: str = "extracted"
    ANALYSIS_DIR: str = "analysis"
    REPORT: str = "report/report.md"

    @staticmethod
    def fetched_document(source_id: str) -> str:
        return f"fetched/{source_id}.json"

    @staticmethod
    def extracted_document(source_id: str) -> str:
        return f"extracted/{source_id}.json"

    @staticmethod
    def analysis_artifact(kind: str, artifact_id: str) -> str:
        return f"analysis/{kind}_{artifact_id}.json"


class ManifestBuilder:
    """Manifest accumulator with deterministic ordering."""

    def __init__(self, *, run_id: str, objective: str, created_at: datetime) -> None:
        self._run_id = run_id
        self._objective = objective
        self._created_at = created_at
        self._artifacts: list[dict[str, str]] = []

    def add(self, *, artifact_id: str, kind: str, path: str) -> None:
        self._artifacts.append({"id": artifact_id, "kind": kind, "path": path})

    def payload(self, *, status: RunStatus, updated_at: datetime | None = None) -> dict[str, object]:
        artifacts = sorted(self._artifacts, key=lambda item: (item["kind"], item["id"], item["path"]))
        return {
            "run_id": self._run_id,
            "objective": self._objective,
            "status": status.value,
            "created_at": self._created_at.isoformat(),
            "updated_at": updated_at.isoformat() if updated_at else None,
            "artifacts": artifacts,
        }

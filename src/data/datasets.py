"""Dataset ingestion contracts for local CSV/JSON inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from src.data.models import ExtractedTable


class DatasetLoader(Protocol):
    """Protocol for table-oriented local dataset loaders."""

    def load(self, path: Path, *, run_id: str) -> ExtractedTable:
        """Load file metadata into a normalized extracted-table representation."""


def load_dataset(path: Path, *, run_id: str) -> ExtractedTable:
    """Placeholder dataset loader contract for future CSV/JSON support."""
    raise NotImplementedError(f"Dataset loading is not implemented yet: {path} (run_id={run_id})")

"""Dataset ingestion placeholders for local CSV/JSON inputs."""

from __future__ import annotations

from pathlib import Path

from src.data.models import ExtractedTable


def load_dataset(path: Path) -> ExtractedTable:
    """Load a local dataset file into normalized table representation."""
    # TODO: Implement CSV/JSON readers and schema normalization.
    raise NotImplementedError

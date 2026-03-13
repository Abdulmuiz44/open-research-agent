"""Content extraction skeleton for fetched web documents."""

from __future__ import annotations

from src.data.models import ExtractedDocument, FetchedDocument


class Extractor:
    """Extracts clean text and metadata from fetched documents."""

    def extract(self, fetched: FetchedDocument) -> ExtractedDocument:
        """Extract normalized document content and metadata."""
        # TODO: Implement Trafilatura + Selectolax fallback extraction.
        raise NotImplementedError

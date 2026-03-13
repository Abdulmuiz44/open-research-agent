"""Analyst agent skeleton for evidence synthesis and comparison."""

from __future__ import annotations

from src.data.models import AnalysisArtifact, ExtractedDocument


class AnalystAgent:
    """Produces analysis artifacts from normalized evidence."""

    def analyze_documents(self, documents: list[ExtractedDocument]) -> list[AnalysisArtifact]:
        """Generate structured findings tied to evidence IDs."""
        # TODO: Implement bounded synthesis and contradiction checks.
        raise NotImplementedError

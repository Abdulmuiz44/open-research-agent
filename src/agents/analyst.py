"""Analyst agent for deterministic evidence synthesis and comparison."""

from __future__ import annotations

from src.analysis.text_analysis import analyze_text
from src.data.models import AnalysisResult, ExtractedDocument


class AnalystAgent:
    """Produces deterministic analysis output from extracted documents."""

    def analyze_documents(self, documents: list[ExtractedDocument]) -> AnalysisResult:
        """Generate structured findings tied to source evidence."""
        return analyze_text(documents)

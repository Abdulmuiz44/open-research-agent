"""Reporter agent for assembling deterministic markdown and JSON reports."""

from __future__ import annotations

from src.analysis.report_builder import build_report
from src.data.models import AnalysisArtifact, Report


class ReporterAgent:
    """Builds final report outputs from analysis artifacts."""

    def build_report(self, run_id: str, objective: str, artifacts: list[AnalysisArtifact], markdown: str) -> Report:
        """Render report sections with deterministic findings and limitations."""
        return build_report(run_id, objective, artifacts, markdown)

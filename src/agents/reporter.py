"""Reporter agent for assembling deterministic markdown and JSON reports."""

from __future__ import annotations

from src.analysis.report_builder import build_report
from src.data.models import AnalysisResult, Report


class ReporterAgent:
    """Builds final report outputs from deterministic analysis results."""

    def build_report(self, run_id: str, objective: str, analysis: AnalysisResult) -> Report:
        """Render report sections with evidence-backed references and limitations."""
        return build_report(run_id=run_id, objective=objective, analysis=analysis)

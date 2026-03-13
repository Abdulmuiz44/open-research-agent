"""Reporter agent skeleton for assembling markdown and JSON reports."""

from __future__ import annotations

from src.data.models import AnalysisArtifact, Report


class ReporterAgent:
    """Builds final report outputs from analysis artifacts."""

    def build_report(self, artifacts: list[AnalysisArtifact]) -> Report:
        """Render report sections with citations and limitations."""
        # TODO: Implement report rendering with citation enforcement.
        raise NotImplementedError

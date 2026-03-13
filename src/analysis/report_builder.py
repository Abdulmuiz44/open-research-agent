"""Report builder skeleton for final markdown and JSON outputs."""

from __future__ import annotations

from src.data.models import AnalysisArtifact, Report


def build_report(run_id: str, objective: str, artifacts: list[AnalysisArtifact]) -> Report:
    """Build a report object from accumulated analysis artifacts."""
    # TODO: Render required report sections and citation mappings.
    raise NotImplementedError

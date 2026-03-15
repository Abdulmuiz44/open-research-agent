"""Reporter agent for assembling deterministic markdown and JSON reports."""

from __future__ import annotations

from datetime import UTC, datetime

from src.analysis import report_builder
from src.data.models import AnalysisArtifact, CandidateSource, ExtractedDocument, Report


class ReporterAgent:
    """Builds final report outputs from run metadata, evidence, and analysis artifacts."""

    def build_report(
        self,
        *,
        run_id: str,
        objective: str,
        extracted_documents: list[ExtractedDocument],
        analysis_artifacts: list[AnalysisArtifact],
        sources: list[CandidateSource],
        generated_at: datetime | None = None,
    ) -> Report:
        """Build a report and enforce the minimum required report sections."""
        report = report_builder.build_report(
            run_id=run_id,
            objective=objective,
            generated_at=generated_at or datetime.now(UTC),
            extracted_documents=extracted_documents,
            analysis_artifacts=analysis_artifacts,
            sources=sources,
        )

        required_sections = [
            "## Title",
            "## Query/Objective",
            "## Run ID",
            "## Generated Timestamp",
            "## Executive Summary",
            "## Key Findings",
            "## Major Themes",
            "## Evidence-Backed Sources",
            "## Limitations",
            "## Suggested Next Steps",
            "## Artifact Summary",
        ]

        for section in required_sections:
            if section not in report.markdown:
                raise ValueError(f"Missing required report section: {section}")

        if not report.title.strip() or not report.executive_summary.strip() or not report.run_id.strip():
            raise ValueError("Report is missing required metadata fields.")

        if report.contradictions_disagreements and "## Contradictions/Disagreements" not in report.markdown:
            raise ValueError("Report has contradictions data but missing markdown contradictions section.")

        return report

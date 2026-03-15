from datetime import UTC, datetime

from src.agents.reporter import ReporterAgent
from src.data.models import AnalysisArtifact, CandidateSource, ExtractedDocument


def test_reporter_agent_build_report_enforces_required_sections() -> None:
    source = CandidateSource(
        run_id="r1",
        query="q",
        url="https://example.com",
        domain="example.com",
        provider="stub",
        provider_rank=1,
    )
    document = ExtractedDocument(
        run_id="r1",
        source_id=source.id,
        source_url="https://example.com",
        content="content",
    )
    artifact = AnalysisArtifact(run_id="r1", summary="Summary")

    report = ReporterAgent().build_report(
        run_id="r1",
        objective="Objective",
        extracted_documents=[document],
        analysis_artifacts=[artifact],
        sources=[source],
        generated_at=datetime(2024, 1, 1, tzinfo=UTC),
    )

    assert "## Title" in report.markdown
    assert "## Artifact Summary" in report.markdown
    assert report.executive_summary == "Summary"

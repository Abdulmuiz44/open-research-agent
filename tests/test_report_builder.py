from datetime import UTC, datetime

from src.analysis.report_builder import build_report
from src.data.models import AnalysisArtifact, CandidateSource, ExtractedDocument


def test_report_builder_contains_required_sections() -> None:
    source = CandidateSource(
        run_id="r1",
        query="q",
        url="https://example.com",
        domain="example.com",
        provider="stub",
        provider_rank=1,
        title="Example Source",
    )
    doc = ExtractedDocument(
        run_id="r1",
        source_id=source.id,
        source_url="https://example.com",
        final_url="https://example.com",
        domain="example.com",
        title="Example",
        raw_content="raw",
        content="clean",
    )
    artifact = AnalysisArtifact(run_id="r1", summary="Deterministic summary")

    report = build_report(
        run_id="r1",
        objective="test objective",
        generated_at=datetime(2024, 1, 1, tzinfo=UTC),
        extracted_documents=[doc],
        analysis_artifacts=[artifact],
        sources=[source],
    )

    assert report.title == "Research Report for test objective"
    assert report.executive_summary == "Deterministic summary"
    assert "## Query/Objective" in report.markdown
    assert "## Key Findings" in report.markdown
    assert "## Evidence-Backed Sources" in report.markdown
    assert "Run ID\nr1" in report.markdown

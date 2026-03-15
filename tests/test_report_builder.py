from src.analysis.report_builder import render_report_markdown
from src.data.models import CandidateSource, ExtractedDocument


def test_report_markdown_contains_required_sections() -> None:
    sources = [
        CandidateSource(
            run_id="r1",
            query="q",
            url="https://example.com",
            domain="example.com",
            provider="stub",
        )
    ]
    docs = [
        ExtractedDocument(
            run_id="r1",
            source_id=sources[0].id,
            source_url="https://example.com",
            final_url="https://example.com",
            domain="example.com",
            title="Example",
            raw_content="raw",
            content="clean",
        )
    ]

    markdown = render_report_markdown(
        run_id="r1",
        objective="test objective",
        summary="summary",
        sources=sources,
        extracted_documents=docs,
        findings=["finding"],
        limitations=["limitation"],
    )
    assert "# Research Report" in markdown
    assert "Run ID: r1" in markdown
    assert "## Summary" in markdown
    assert "## Counts" in markdown
    assert "Extracted documents: 1" in markdown
    assert "## Key Findings" in markdown
    assert "## Limitations" in markdown
    assert "## Evidence" in markdown

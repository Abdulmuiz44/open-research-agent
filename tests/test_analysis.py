from __future__ import annotations

from src.analysis.text_analysis import analyze_text
from src.data.models import ExtractedDocument


def _doc(run_id: str, source_id: str, url: str, content: str) -> ExtractedDocument:
    return ExtractedDocument(
        run_id=run_id,
        source_id=source_id,
        content=content,
        metadata={"final_url": url},
    )


def test_deterministic_analysis_findings_and_themes() -> None:
    docs = [
        _doc("r1", "s1", "https://a.test", "AI market growth reached 10 in 2024. Pricing changed this year."),
        _doc("r1", "s2", "https://b.test", "Market analysts reported growth of 12 in 2024 and new pricing tiers."),
        _doc("r1", "s3", "https://c.test", "Cloud market growth remains a major topic for vendors."),
    ]

    result = analyze_text(docs)

    assert result.summary.total_documents == 3
    assert result.findings
    assert result.themes
    assert result.findings[0].supporting_source_ids
    assert result.findings[0].supporting_source_urls


def test_contradiction_detection_simple_fixture() -> None:
    docs = [
        _doc("r2", "s1", "https://a.test", "The price is 10 dollars for the base plan."),
        _doc("r2", "s2", "https://b.test", "The price is 20 dollars for the base plan."),
    ]

    result = analyze_text(docs)

    assert len(result.contradictions) == 1
    assert result.contradictions[0].topic in {"price", "pricing"}

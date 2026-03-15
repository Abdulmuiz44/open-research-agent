"""Report builder for final markdown and JSON outputs."""

from __future__ import annotations

from datetime import UTC, datetime

from src.data.models import AnalysisArtifact, CandidateSource, ExtractedDocument, Report


def render_report_markdown(
    *,
    run_id: str,
    objective: str,
    summary: str,
    sources: list[CandidateSource],
    extracted_documents: list[ExtractedDocument],
    findings: list[str],
    limitations: list[str],
) -> str:
    """Render deterministic markdown report for local artifact inspection."""
    evidence_lines = []
    for index, document in enumerate(extracted_documents[:5], start=1):
        source = next((item for item in sources if item.id == document.source_id), None)
        url = str(document.final_url or document.source_url)
        title = document.title or (source.title if source else "Untitled source") or "Untitled source"
        evidence_lines.append(f"- [{index}] {title} ({url})")

    markdown_lines = [
        "# Research Report",
        f"- Query: {objective}",
        f"- Run ID: {run_id}",
        f"- Saved at: {datetime.now(UTC).isoformat()}",
        "",
        "## Summary",
        summary,
        "",
        "## Counts",
        f"- Sources discovered: {len(sources)}",
        f"- Extracted documents: {len(extracted_documents)}",
        "",
        "## Key Findings",
    ]
    markdown_lines.extend([f"- {finding}" for finding in findings] or ["- No findings generated."])
    markdown_lines.extend(["", "## Limitations"])
    markdown_lines.extend([f"- {item}" for item in limitations])
    markdown_lines.extend(["", "## Evidence"])
    markdown_lines.extend(evidence_lines or ["- No extracted evidence available."])
    return "\n".join(markdown_lines)


def build_report(run_id: str, objective: str, artifacts: list[AnalysisArtifact], markdown: str) -> Report:
    """Build report payload from analysis artifacts and markdown."""
    findings = [artifact.summary for artifact in artifacts if artifact.summary]
    limitations = ["Analysis is deterministic and lightweight in this MVP stage."]
    return Report(run_id=run_id, objective=objective, findings=findings, limitations=limitations, markdown=markdown)

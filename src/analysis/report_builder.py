"""Report builder for deterministic markdown and structured report outputs."""

from __future__ import annotations

from datetime import datetime

from src.data.models import AnalysisArtifact, CandidateSource, ExtractedDocument, Report


def _sorted_sources(sources: list[CandidateSource]) -> list[CandidateSource]:
    return sorted(sources, key=lambda item: (item.provider_rank, str(item.url), item.id))


def _sorted_documents(documents: list[ExtractedDocument]) -> list[ExtractedDocument]:
    return sorted(documents, key=lambda item: (str(item.final_url or item.source_url), item.id))


def _sorted_artifacts(artifacts: list[AnalysisArtifact]) -> list[AnalysisArtifact]:
    return sorted(artifacts, key=lambda item: (item.kind.value, item.id))


def _as_bullets(items: list[str], fallback: str) -> list[str]:
    return [f"- {item}" for item in items] or [f"- {fallback}"]


def build_report(
    *,
    run_id: str,
    objective: str,
    generated_at: datetime,
    extracted_documents: list[ExtractedDocument],
    analysis_artifacts: list[AnalysisArtifact],
    sources: list[CandidateSource],
) -> Report:
    """Build a deterministic report with required structured sections and markdown."""
    ordered_sources = _sorted_sources(sources)
    ordered_documents = _sorted_documents(extracted_documents)
    ordered_artifacts = _sorted_artifacts(analysis_artifacts)

    source_by_id = {source.id: source for source in ordered_sources}

    key_findings = [artifact.summary.strip() for artifact in ordered_artifacts if artifact.summary.strip()]
    executive_summary = key_findings[0] if key_findings else "No summary available from analysis artifacts."

    major_themes: list[str] = []
    contradictions: list[str] = []
    for artifact in ordered_artifacts:
        metadata = getattr(artifact, "metadata", {}) if hasattr(artifact, "metadata") else {}
        for theme in metadata.get("major_themes", []):
            if theme not in major_themes:
                major_themes.append(theme)
        for contradiction in metadata.get("contradictions", []):
            if contradiction not in contradictions:
                contradictions.append(contradiction)

    evidence_backed_sources: list[str] = []
    seen_source_urls: set[str] = set()
    for document in ordered_documents:
        source = source_by_id.get(document.source_id)
        resolved_url = str(document.final_url or document.source_url)
        source_title = document.title or (source.title if source else None) or "Untitled source"
        evidence_line = f"{source_title} ({resolved_url})"
        if evidence_line not in seen_source_urls:
            seen_source_urls.add(evidence_line)
            evidence_backed_sources.append(evidence_line)

    limitations = ["Analysis is deterministic and limited to fetched and extracted evidence in this run."]
    if not ordered_documents:
        limitations.append("No extracted documents were available, so evidence coverage is limited.")

    next_steps = [
        "Validate key findings with additional high-quality primary sources.",
        "Run another pass with refined constraints if the objective requires deeper coverage.",
    ]

    artifact_summary = [
        f"Artifacts analyzed: {len(ordered_artifacts)}",
        f"Sources considered: {len(ordered_sources)}",
        f"Extracted documents: {len(ordered_documents)}",
    ]

    markdown_lines = [
        "# Research Report",
        "",
        "## Title",
        f"Research Report for {objective}",
        "",
        "## Query/Objective",
        objective,
        "",
        "## Run ID",
        run_id,
        "",
        "## Generated Timestamp",
        generated_at.isoformat(),
        "",
        "## Executive Summary",
        executive_summary,
        "",
        "## Key Findings",
        *_as_bullets(key_findings, "No key findings generated."),
        "",
        "## Major Themes",
        *_as_bullets(major_themes, "No major themes identified."),
    ]

    if contradictions:
        markdown_lines.extend(["", "## Contradictions/Disagreements", *_as_bullets(contradictions, "")])

    markdown_lines.extend(
        [
            "",
            "## Evidence-Backed Sources",
            *_as_bullets(evidence_backed_sources, "No extracted evidence available."),
            "",
            "## Limitations",
            *_as_bullets(limitations, "No limitations captured."),
            "",
            "## Suggested Next Steps",
            *_as_bullets(next_steps, "No suggested next steps."),
            "",
            "## Artifact Summary",
            *_as_bullets(artifact_summary, "No artifacts summarized."),
        ]
    )

    title = f"Research Report for {objective}"
    return Report(
        run_id=run_id,
        objective=objective,
        title=title,
        generated_at=generated_at,
        executive_summary=executive_summary,
        findings=key_findings,
        major_themes=major_themes,
        contradictions_disagreements=contradictions,
        evidence_backed_sources=evidence_backed_sources,
        limitations=limitations,
        suggested_next_steps=next_steps,
        artifact_summary=artifact_summary,
        markdown="\n".join(markdown_lines),
    )

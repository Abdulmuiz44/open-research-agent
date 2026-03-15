"""Deterministic report builder for final markdown output."""

from __future__ import annotations

from src.data.models import AnalysisResult, Report


def build_report(run_id: str, objective: str, analysis: AnalysisResult) -> Report:
    """Build a report object from deterministic analysis outputs."""
    top_findings = analysis.findings[:5]

    finding_lines = []
    for finding in top_findings:
        refs = ", ".join(finding.supporting_source_urls[:3]) or "no source URLs"
        finding_lines.append(f"- **{finding.title}** ({finding.theme or 'general'}, confidence={finding.confidence})")
        finding_lines.append(f"  - {finding.summary}")
        finding_lines.append(f"  - Sources: {refs}")

    theme_lines = [f"- {theme.label} ({len(theme.source_ids)} sources)" for theme in analysis.themes[:8]]
    contradiction_lines = (
        [f"- {item.summary}" for item in analysis.contradictions]
        if analysis.contradictions
        else ["- No obvious contradictions detected by conservative heuristics."]
    )
    limitations = analysis.summary.limitations or ["Deterministic heuristics may miss nuanced claims."]

    markdown = "\n".join(
        [
            "# Research Report",
            "",
            f"## Objective\n{objective}",
            "",
            f"## Analysis Summary\n{analysis.summary.summary}",
            "",
            "## Top Findings",
            *finding_lines,
            "",
            "## Major Themes",
            *theme_lines,
            "",
            "## Contradictions / Disagreements",
            *contradiction_lines,
            "",
            "## Limitations",
            *[f"- {item}" for item in limitations],
        ]
    )

    return Report(
        run_id=run_id,
        objective=objective,
        findings=[finding.summary for finding in top_findings],
        limitations=limitations,
        markdown=markdown,
    )

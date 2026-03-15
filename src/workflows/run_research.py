"""Research workflow orchestration for bounded local runs."""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.data.models import (
    AnalysisArtifact,
    ArtifactKind,
    CandidateSource,
    ExtractedDocument,
    FetchMethod,
    FetchedDocument,
    ResearchPlan,
    ResearchRun,
    RunStatus,
    Source,
)
from src.data.storage import LocalStorageStub, StorageBackend
from src.search.provider import build_search_provider
from src.search.queries import build_queries
from src.web.crawler import Crawler
from src.web.extractor import Extractor


class RunResearchInput(BaseModel):
    """Inputs required to kick off a bounded research workflow run."""

    objective: str = Field(min_length=3)
    constraints: list[str] = Field(default_factory=list)
    max_sources: int = Field(default=10, ge=1, le=100)


class RunResearchOutput(BaseModel):
    """Top-level workflow output with stage artifacts."""

    run: ResearchRun
    plan: ResearchPlan
    search_queries: list[str]
    discovered_sources: list[CandidateSource]
    fetched_documents: list[FetchedDocument]
    extracted_documents: list[ExtractedDocument]
    analysis_artifacts: list[AnalysisArtifact]
    report_markdown: str
    fetched_http_count: int = 0
    fetched_browser_count: int = 0
    fallback_trigger_count: int = 0
    extraction_status_summary: dict[str, int] = Field(default_factory=dict)
    artifact_paths: dict[str, str] = Field(default_factory=dict)


def initialize_run(payload: RunResearchInput) -> ResearchRun:
    """Create initial run metadata before stage orchestration."""
    return ResearchRun(objective=payload.objective)


def _build_plan(payload: RunResearchInput) -> ResearchPlan:
    objectives = [payload.objective, *payload.constraints]
    return ResearchPlan(
        objective=payload.objective,
        research_objectives=objectives[:3],
        source_budget=min(payload.max_sources, get_settings().max_sources_per_run),
    )


def _save_run_artifacts(
    run_id: str,
    fetched: list[FetchedDocument],
    extracted: list[ExtractedDocument],
    report_markdown: str,
) -> dict[str, str]:
    settings = get_settings()
    run_dir = Path(settings.artifacts_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    fetch_path = run_dir / "fetch_metadata.json"
    extraction_path = run_dir / "extraction_summary.json"
    report_path = run_dir / "report.md"

    fetch_payload = [
        {
            "source_id": doc.source_id,
            "requested_url": str(doc.requested_url),
            "final_url": str(doc.final_url) if doc.final_url else None,
            "fetch_method": doc.fetch_method,
            "fetch_outcome": doc.fetch_outcome,
            "fallback_triggered": doc.fallback_triggered,
            "fallback_reason": doc.fallback_reason,
            "status_code": doc.status_code,
            "rendered_content_available": doc.rendered_content_available,
            "content_length": doc.content_length,
            "error": doc.error,
        }
        for doc in fetched
    ]
    extraction_payload = [
        {
            "source_id": doc.source_id,
            "title": doc.title,
            "text_length": doc.text_length,
            "extraction_quality": doc.extraction_quality,
            "metadata": doc.metadata,
        }
        for doc in extracted
    ]

    fetch_path.write_text(json.dumps(fetch_payload, indent=2, default=str), encoding="utf-8")
    extraction_path.write_text(json.dumps(extraction_payload, indent=2, default=str), encoding="utf-8")
    report_path.write_text(report_markdown, encoding="utf-8")

    return {
        "artifact_dir": str(run_dir),
        "fetch_metadata": str(fetch_path),
        "extraction_summary": str(extraction_path),
        "report": str(report_path),
    }


def run_research_workflow(
    payload: RunResearchInput,
    storage: StorageBackend | None = None,
) -> RunResearchOutput:
    """Execute bounded local discovery, fetch, extract, and simple analysis/reporting."""
    backend = storage or LocalStorageStub()
    run = backend.create_run(initialize_run(payload))
    backend.update_run_status(run.id, RunStatus.RUNNING)

    try:
        plan = _build_plan(payload)
        queries = build_queries(plan)

        provider = build_search_provider(get_settings())
        crawler = Crawler(provider)
        discovered = crawler.discover(run.id, queries)

        fetched = asyncio.run(crawler.fetch(discovered))
        extractor = Extractor()
        extracted = [extractor.extract(doc) for doc in fetched if doc.success and (doc.raw_html or doc.text)]

        for source in discovered:
            backend.save_source(
                Source(
                    id=source.id,
                    run_id=source.run_id,
                    url=source.url,
                    domain=source.domain,
                    title=source.title,
                )
            )
        for document in fetched:
            backend.save_fetched_document(document)
        for document in extracted:
            backend.save_extracted_document(document)

        fetched_http_count = len([doc for doc in fetched if doc.fetch_method == FetchMethod.HTTP])
        fetched_browser_count = len([doc for doc in fetched if doc.fetch_method == FetchMethod.BROWSER])
        fallback_trigger_count = len([doc for doc in fetched if doc.fallback_triggered])
        extraction_status_summary = dict(Counter([doc.extraction_quality for doc in extracted]))

        summary = (
            f"Discovered {len(discovered)} sources, fetched {len([d for d in fetched if d.success])}, "
            f"browser fallback used for {fallback_trigger_count}, extracted {len(extracted)} documents."
        )
        artifact = AnalysisArtifact(
            run_id=run.id,
            kind=ArtifactKind.SUMMARY,
            summary=summary,
            evidence_ids=[doc.id for doc in extracted],
        )
        backend.save_analysis_artifact_metadata(artifact)

        report_lines = [
            f"# Research Report\n\nObjective: {run.objective}",
            f"\n## Method\n- queries: {', '.join(queries)}",
            f"\n## Findings\n- {summary}",
            "\n## Limitations\n- Workflow is bounded to HTTP-first fetch with single-page browser fallback.",
        ]
        report_markdown = "\n".join(report_lines)
        artifact_paths = _save_run_artifacts(run.id, fetched, extracted, report_markdown)
        backend.set_run_artifact_paths(run.id, artifact_paths)

        run = backend.update_run_status(run.id, RunStatus.COMPLETED)
        return RunResearchOutput(
            run=run,
            plan=plan,
            search_queries=queries,
            discovered_sources=discovered,
            fetched_documents=fetched,
            extracted_documents=extracted,
            analysis_artifacts=[artifact],
            report_markdown=report_markdown,
            fetched_http_count=fetched_http_count,
            fetched_browser_count=fetched_browser_count,
            fallback_trigger_count=fallback_trigger_count,
            extraction_status_summary=extraction_status_summary,
            artifact_paths=artifact_paths,
        )
    except Exception:
        run = backend.update_run_status(run.id, RunStatus.FAILED)
        raise

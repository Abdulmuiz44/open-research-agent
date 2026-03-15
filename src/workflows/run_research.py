"""Research workflow orchestration for bounded local runs."""

from __future__ import annotations

import asyncio

from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.data.models import (
    AnalysisArtifact,
    ArtifactKind,
    CandidateSource,
    ExtractedDocument,
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
        for document in extracted:
            backend.save_extracted_document(document)

        summary = (
            f"Discovered {len(discovered)} sources, fetched {len([d for d in fetched if d.success])}, "
            f"extracted {len(extracted)} documents."
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
            "\n## Limitations\n- Analysis is deterministic and lightweight in this MVP stage.",
        ]
        report_markdown = "\n".join(report_lines)

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
        )
    except Exception as exc:
        run = backend.update_run_status(run.id, RunStatus.FAILED, error_message=str(exc))
        raise

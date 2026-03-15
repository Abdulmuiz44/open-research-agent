from __future__ import annotations

from src.data.models import CandidateSource, FetchedDocument
from src.search.provider import StubSearchProvider
from src.workflows import run_research as workflow_module
from src.workflows.run_research import RunResearchInput, run_research_workflow


def test_workflow_success_with_stub_provider(monkeypatch) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    output = run_research_workflow(RunResearchInput(objective="test objective", max_sources=2))
    assert output.run.status.value == "completed"
    assert output.search_queries
    assert output.discovered_sources == []
    assert output.analysis.summary.total_documents == 0


def test_workflow_analysis_artifacts_written(monkeypatch) -> None:
    workflow_module.get_settings.cache_clear()

    def _discover(self, run_id: str, queries: list[str]) -> list[CandidateSource]:
        _ = queries
        return [
            CandidateSource(
                id="source-1",
                run_id=run_id,
                query="q",
                url="https://example.com/a",
                domain="example.com",
                provider="stub",
            )
        ]

    async def _fetch(self, sources: list[CandidateSource]) -> list[FetchedDocument]:
        return [
            FetchedDocument(
                run_id=sources[0].run_id,
                source_id=sources[0].id,
                requested_url=sources[0].url,
                final_url=sources[0].url,
                success=True,
                raw_html="<html><title>A</title><body>Market growth was 10. Price is 10 dollars.</body></html>",
            )
        ]

    monkeypatch.setattr(workflow_module.Crawler, "discover", _discover)
    monkeypatch.setattr(workflow_module.Crawler, "fetch", _fetch)
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())

    output = run_research_workflow(RunResearchInput(objective="artifact objective", max_sources=1))

    assert output.analysis.findings
    assert output.artifact_dir.endswith("/analysis")
    assert output.report_path.endswith("/report.md")

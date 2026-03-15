from __future__ import annotations

from src.data.models import CandidateSource, FetchMethod, FetchOutcome, FetchedDocument
from src.data.storage import LocalStorageStub
from src.search.provider import SearchProvider, StubSearchProvider
from src.workflows import run_research as workflow_module
from src.workflows.run_research import RunResearchInput, run_research_workflow


class SingleSourceProvider(SearchProvider):
    def search(self, run_id: str, query: str, limit: int = 10) -> list[CandidateSource]:
        _ = (query, limit)
        return [
            CandidateSource(
                run_id=run_id,
                query="q",
                url="https://example.com/article",
                domain="example.com",
                title="Example",
                provider="test",
                provider_rank=1,
            )
        ]


def test_workflow_success_with_stub_provider(monkeypatch) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    output = run_research_workflow(RunResearchInput(objective="test objective", max_sources=2))
    assert output.run.status.value == "completed"
    assert output.search_queries
    assert output.discovered_sources == []


def test_workflow_http_success_without_fallback(monkeypatch) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: SingleSourceProvider())

    async def fake_fetch_one(self, source):
        return FetchedDocument(
            run_id=source.run_id,
            source_id=source.id,
            requested_url=source.url,
            raw_html="<html><head><title>T</title></head><body><p>" + ("word " * 400) + "</p></body></html>",
            success=True,
            fetch_method=FetchMethod.HTTP,
            fetch_outcome=FetchOutcome.SUCCESS,
        )

    monkeypatch.setattr(workflow_module.Crawler, "fetch_one", fake_fetch_one)
    storage = LocalStorageStub()
    output = run_research_workflow(RunResearchInput(objective="test objective", max_sources=1), storage=storage)
    assert output.fetched_http_count == 1
    assert output.fetched_browser_count == 0
    assert output.fallback_trigger_count == 0
    assert output.extracted_documents
    assert output.artifact_paths["fetch_metadata"]
    assert storage.get_run_artifact_paths(output.run.id)["report"]


def test_workflow_browser_fallback_path(monkeypatch) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: SingleSourceProvider())

    async def fake_fetch_one(self, source):
        return FetchedDocument(
            run_id=source.run_id,
            source_id=source.id,
            requested_url=source.url,
            raw_html="<html><head><title>Rendered</title></head><body><main>" + ("content " * 300) + "</main></body></html>",
            success=True,
            fetch_method=FetchMethod.BROWSER,
            fetch_outcome=FetchOutcome.SUCCESS,
            fallback_triggered=True,
            fallback_reason="near_empty_content",
            rendered_content_available=True,
        )

    monkeypatch.setattr(workflow_module.Crawler, "fetch_one", fake_fetch_one)
    output = run_research_workflow(RunResearchInput(objective="test objective", max_sources=1))
    assert output.fetched_http_count == 0
    assert output.fetched_browser_count == 1
    assert output.fallback_trigger_count == 1
    assert output.extraction_status_summary

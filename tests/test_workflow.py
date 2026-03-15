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

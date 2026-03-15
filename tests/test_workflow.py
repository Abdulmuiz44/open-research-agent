from pathlib import Path

from src.data.storage import LocalStorageStub
from src.search.provider import StubSearchProvider
from src.workflows import run_research as workflow_module
from src.workflows.run_research import RunResearchInput, run_research_workflow


def test_workflow_success_with_stub_provider(monkeypatch, tmp_path: Path) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    storage = LocalStorageStub(base_dir=tmp_path / "runs")
    output = run_research_workflow(RunResearchInput(objective="test objective", max_sources=2), storage=storage)
    assert output.run.status.value == "completed"
    assert output.search_queries
    assert output.discovered_sources == []
    assert (Path(output.artifact_dir) / "manifest.json").exists()
    assert "report" in output.artifact_refs
    assert output.artifact_paths

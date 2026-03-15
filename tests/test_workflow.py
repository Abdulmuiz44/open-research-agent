from pathlib import Path
import json

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


def test_manifest_matches_saved_metadata_refs(monkeypatch, tmp_path: Path) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    storage = LocalStorageStub(base_dir=tmp_path / "runs")

    output = run_research_workflow(RunResearchInput(objective="artifact consistency", max_sources=2), storage=storage)

    manifest = json.loads((Path(output.artifact_dir) / "manifest.json").read_text(encoding="utf-8"))
    artifact_entries = manifest["artifacts"]
    artifact_paths = {entry["path"] for entry in artifact_entries}
    ref_paths = set(output.artifact_refs.values())

    assert artifact_entries
    assert all("id" in entry and "kind" in entry and "path" in entry for entry in artifact_entries)
    assert "manifest" in {entry["kind"] for entry in artifact_entries}
    assert artifact_paths.issubset(ref_paths)

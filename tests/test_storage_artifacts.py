import json
from pathlib import Path

from src.core.config import Settings
from src.data.models import ExtractedDocument
from src.data.storage import LocalStorageStub, SQLiteStorageBackend
from src.search.provider import StubSearchProvider
from src.workflows import run_research as workflow_module
from src.workflows.run_research import RunResearchInput, run_research_workflow


def test_storage_saves_extracted_and_lists_artifacts(tmp_path: Path) -> None:
    storage = LocalStorageStub(base_dir=tmp_path / "runs")
    run_id = "run-storage"
    storage.save_artifact_json(run_id, "manifest.json", {"run_id": run_id})

    doc = ExtractedDocument(
        run_id=run_id,
        source_id="s1",
        source_url="https://example.com",
        final_url="https://example.com",
        domain="example.com",
        title="x",
        raw_content="raw",
        content="clean",
    )
    storage.save_extracted_document(doc)

    artifacts = storage.list_run_artifacts(run_id)
    assert "manifest.json" in artifacts
    assert any(path.startswith("extracted/") for path in artifacts)
    assert storage.get_run_artifact_refs(run_id)


def test_sqlite_storage_create_and_retrieve_lifecycle(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "storage.db"
    runs_dir = tmp_path / "runs"

    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    monkeypatch.setattr(workflow_module, "get_settings", lambda: Settings(runs_dir=runs_dir))

    storage = SQLiteStorageBackend(db_path=db_path, base_dir=runs_dir)
    output = run_research_workflow(
        RunResearchInput(objective="sqlite lifecycle test", max_sources=2),
        storage=storage,
    )

    run = storage.get_run(output.run.id)
    assert run is not None
    assert run.id == output.run.id
    assert run.status.value == "completed"
    artifacts = storage.list_run_artifacts(output.run.id)
    assert "manifest.json" in artifacts
    assert "report/report.md" in artifacts


def test_sqlite_storage_reinitialization_retains_run_and_artifacts(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "storage.db"
    runs_dir = tmp_path / "runs"

    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    monkeypatch.setattr(workflow_module, "get_settings", lambda: Settings(runs_dir=runs_dir))

    first_storage = SQLiteStorageBackend(db_path=db_path, base_dir=runs_dir)
    output = run_research_workflow(
        RunResearchInput(objective="persist me", max_sources=2),
        storage=first_storage,
    )

    second_storage = SQLiteStorageBackend(db_path=db_path, base_dir=runs_dir)
    reloaded_run = second_storage.get_run(output.run.id)
    reloaded_artifacts = second_storage.list_run_artifacts(output.run.id)
    reloaded_refs = second_storage.get_run_artifact_refs(output.run.id)

    assert reloaded_run is not None
    assert reloaded_run.id == output.run.id
    assert reloaded_run.status.value == "completed"
    assert "manifest.json" in reloaded_artifacts
    assert reloaded_refs["report"].endswith("report/report.md")


def test_manifest_paths_match_persisted_artifacts(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "storage.db"
    runs_dir = tmp_path / "runs"

    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    monkeypatch.setattr(workflow_module, "get_settings", lambda: Settings(runs_dir=runs_dir))

    storage = SQLiteStorageBackend(db_path=db_path, base_dir=runs_dir)
    output = run_research_workflow(RunResearchInput(objective="manifest check", max_sources=2), storage=storage)

    manifest_path = runs_dir / output.run.id / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = set(storage.list_run_artifacts(output.run.id))
    refs = storage.get_run_artifact_refs(output.run.id)

    assert set(manifest["paths"]).issuperset({"plan", "sources", "fetched", "extracted", "report", "final_result"})
    assert set(manifest["paths"][key].split(f"/{output.run.id}/", maxsplit=1)[1] for key in manifest["paths"]) <= artifacts
    assert manifest["paths"]["report"] == refs["report"]

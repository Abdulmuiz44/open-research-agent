"""Packaging file existence and baseline correctness checks."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_exists_and_uses_fastapi_entrypoint() -> None:
    dockerfile = ROOT / "Dockerfile"
    assert dockerfile.exists()
    content = dockerfile.read_text(encoding="utf-8")
    assert "apps.api.main:app" in content
    assert "python:3.11-slim" in content


def test_compose_exists_and_mounts_outputs() -> None:
    compose = ROOT / "compose.yaml"
    assert compose.exists()
    content = compose.read_text(encoding="utf-8")
    assert "./outputs:/app/outputs" in content
    assert "env_file" in content


def test_dockerignore_excludes_outputs() -> None:
    dockerignore = ROOT / ".dockerignore"
    assert dockerignore.exists()
    content = dockerignore.read_text(encoding="utf-8")
    assert "outputs/" in content

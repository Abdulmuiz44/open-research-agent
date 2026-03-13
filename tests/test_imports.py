"""Smoke tests for scaffold importability."""

from __future__ import annotations


def test_core_imports() -> None:
    """Ensure core module imports resolve."""
    import src.core.config  # noqa: F401
    import src.core.exceptions  # noqa: F401
    import src.core.logging  # noqa: F401


def test_workflow_imports() -> None:
    """Ensure workflow-level modules import."""
    import src.workflows.run_research  # noqa: F401

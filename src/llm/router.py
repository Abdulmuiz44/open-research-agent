"""LLM routing shell for model/provider selection."""

from __future__ import annotations

from dataclasses import dataclass

from src.core.config import Settings


@dataclass(frozen=True)
class ModelRoute:
    """Provider and model selection details for a workflow stage."""

    provider: str
    model: str


class LLMRouter:
    """Resolves model routing from settings without calling external APIs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def route_for_stage(self, stage: str) -> ModelRoute:
        """Resolve the configured model route for the requested stage."""
        if stage == "planning":
            return ModelRoute(provider="openai", model=self._settings.planner_model)
        if stage == "analysis":
            return ModelRoute(provider="openai", model=self._settings.analysis_model)
        return ModelRoute(provider="openai", model=self._settings.default_model)

    def complete(self, prompt: str, *, stage: str = "default") -> str:
        """Placeholder completion API contract for future provider integration."""
        route = self.route_for_stage(stage)
        raise NotImplementedError(
            f"LLM completion is not implemented yet (provider={route.provider}, model={route.model})."
        )

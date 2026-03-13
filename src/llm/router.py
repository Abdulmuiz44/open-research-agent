"""LLM routing abstraction for model/provider selection."""

from __future__ import annotations

from typing import Any


class LLMRouter:
    """Chooses model/provider settings for each pipeline stage."""

    def complete(self, prompt: str, *, model: str | None = None) -> dict[str, Any]:
        """Generate completion response for a prompt."""
        # TODO: Integrate LiteLLM/PydanticAI provider routing.
        raise NotImplementedError

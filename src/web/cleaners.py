"""Text cleanup helpers for extracted content."""

from __future__ import annotations


def normalize_whitespace(text: str) -> str:
    """Normalize excessive whitespace in extracted text."""
    # TODO: Extend with additional deterministic cleanup rules.
    return " ".join(text.split())

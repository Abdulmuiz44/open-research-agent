"""Text cleaning helpers for extracted web content."""

from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and trim edges."""
    return re.sub(r"\s+", " ", text).strip()


def trim_text(text: str, max_chars: int = 8000) -> str:
    """Bound extracted content length for deterministic downstream analysis."""
    return text[:max_chars].strip()

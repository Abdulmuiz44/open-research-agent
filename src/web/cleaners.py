"""Text cleaning helpers for extracted web content."""

from __future__ import annotations

import re


BOILERPLATE_PATTERNS = [
    r"\bcookie policy\b",
    r"\bprivacy policy\b",
    r"\bterms of service\b",
    r"\ball rights reserved\b",
    r"\bsubscribe\b",
]


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and trim edges."""
    return re.sub(r"\s+", " ", text).strip()


def remove_boilerplate_lines(text: str) -> str:
    """Drop obviously noisy lines while keeping extraction deterministic."""
    if not text:
        return ""

    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = normalize_whitespace(raw_line)
        if not line:
            continue
        lower = line.lower()
        if any(re.search(pattern, lower) for pattern in BOILERPLATE_PATTERNS):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def trim_text(text: str, max_chars: int = 12000) -> str:
    """Bound extracted content length for deterministic downstream analysis."""
    return text[:max_chars].strip()

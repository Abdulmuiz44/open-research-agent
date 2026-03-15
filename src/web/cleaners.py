"""Text cleaning helpers for extracted web content."""

from __future__ import annotations

import re


BOILERPLATE_PATTERNS = [
    r"\bcookie(s)?\b",
    r"\bprivacy policy\b",
    r"\bterms of service\b",
    r"\bsubscribe\b",
    r"\bsign up\b",
    r"\ball rights reserved\b",
]


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and trim edges."""
    return re.sub(r"\s+", " ", text).strip()


def remove_boilerplate_lines(text: str) -> str:
    """Remove short repeated boilerplate/navigation-style lines."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned: list[str] = []
    for line in lines:
        lowered = line.lower()
        if len(line) < 3:
            continue
        if any(re.search(pattern, lowered) for pattern in BOILERPLATE_PATTERNS):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def trim_text(text: str, max_chars: int = 8000) -> str:
    """Bound extracted content length for deterministic downstream analysis."""
    return text[:max_chars].strip()

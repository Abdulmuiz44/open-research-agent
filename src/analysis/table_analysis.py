"""Tabular analysis helpers for local and extracted table data."""

from __future__ import annotations

from src.data.models import ExtractedTable


def analyze_tables(tables: list[ExtractedTable]) -> dict[str, int]:
    """Return bounded deterministic table-level counts for report context."""
    if not tables:
        return {"table_count": 0, "total_rows": 0}
    return {
        "table_count": len(tables),
        "total_rows": sum(table.row_count for table in tables),
    }

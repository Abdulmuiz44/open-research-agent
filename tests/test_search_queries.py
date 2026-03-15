from src.data.models import ResearchPlan
from src.search.queries import build_queries, normalize_query


def test_normalize_query() -> None:
    assert normalize_query("  Hello,   WORLD!! ") == "hello world"


def test_build_queries_bounded_unique() -> None:
    plan = ResearchPlan(objective="Test Objective", research_objectives=["Alpha", "Alpha"], search_queries=["Beta"])
    queries = build_queries(plan)
    assert queries
    assert len(queries) <= 6
    assert len(queries) == len(set(queries))

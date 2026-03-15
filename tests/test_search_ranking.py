from src.data.models import CandidateSource
from src.search.ranker import deduplicate_sources, rank_sources


def _source(url: str, score: float, rank: int) -> CandidateSource:
    return CandidateSource(
        run_id="run-1",
        query="q",
        url=url,
        domain="example.com",
        title="title",
        provider="test",
        provider_rank=rank,
        score=score,
    )


def test_deduplicate_sources_by_canonical_url() -> None:
    sources = [_source("https://example.com/path", 0.4, 2), _source("https://example.com/path/", 0.8, 1)]
    deduped = deduplicate_sources(sources)
    assert len(deduped) == 1
    assert deduped[0].score == 0.8


def test_rank_sources_returns_top_n() -> None:
    sources = [_source(f"https://example.com/{idx}", 0.1, idx) for idx in range(1, 6)]
    ranked = rank_sources(sources, top_n=3)
    assert len(ranked) == 3
    assert ranked[0].score >= ranked[-1].score

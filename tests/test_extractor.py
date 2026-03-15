from pathlib import Path

from src.data.models import FetchMethod, FetchOutcome, FetchedDocument
from src.web.extractor import Extractor


def _fixture(name: str) -> str:
    return Path("tests/fixtures") .joinpath(name).read_text(encoding="utf-8")


def test_extractor_shape_from_html() -> None:
    fetched = FetchedDocument(
        run_id="run-1",
        source_id="source-1",
        requested_url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        content_type="text/html",
        raw_html=_fixture("simple_static.html"),
        success=True,
        fetch_method=FetchMethod.HTTP,
        fetch_outcome=FetchOutcome.SUCCESS,
    )
    extracted = Extractor().extract(fetched)
    assert extracted.title == "Simple Page"
    assert "simple static content" in extracted.content.lower()
    assert extracted.content_hash
    assert extracted.text_length > 30


def test_extractor_removes_noisy_boilerplate() -> None:
    fetched = FetchedDocument(
        run_id="run-2",
        source_id="source-2",
        requested_url="https://example.com/noisy",
        raw_html=_fixture("noisy_page.html"),
        success=True,
        fetch_method=FetchMethod.BROWSER,
        fetch_outcome=FetchOutcome.SUCCESS,
        fallback_triggered=True,
        fallback_reason="near_empty_content",
        rendered_content_available=True,
    )
    extracted = Extractor().extract(fetched)
    assert extracted.title == "OG Noisy Article"
    assert "cookie policy" not in extracted.content.lower()
    assert extracted.metadata["fetch_method"] == FetchMethod.BROWSER
    assert extracted.metadata["fallback_triggered"] is True

from pathlib import Path

from src.data.models import ExtractionStatus, FetchedDocument
from src.web.cleaners import normalize_whitespace, remove_boilerplate_lines
from src.web.extractor import Extractor


def _fixture(name: str) -> str:
    return (Path(__file__).parent / "fixtures" / "html" / name).read_text(encoding="utf-8")


def test_extractor_shape_from_html() -> None:
    fetched = FetchedDocument(
        run_id="run-1",
        source_id="source-1",
        requested_url="https://example.com",
        final_url="https://example.com/articles/simple",
        status_code=200,
        content_type="text/html",
        raw_html=_fixture("simple_article.html"),
        success=True,
    )
    extracted = Extractor().extract(fetched)
    assert extracted.title == "Simple Article"
    assert "Hello world" in extracted.content
    assert extracted.metadata["canonical_url"] == "https://example.com/articles/simple"
    assert extracted.metadata["meta_description"] == "Simple page description"
    assert extracted.metadata["publish_date"] == "2025-01-05"
    assert extracted.extraction_status == ExtractionStatus.SUCCESS
    assert extracted.content_hash


def test_cleaning_removes_boilerplate() -> None:
    noisy = _fixture("noisy_page.html")
    cleaned = remove_boilerplate_lines(normalize_whitespace(noisy))
    assert "Subscribe now" not in cleaned
    assert "Cookie policy" not in cleaned


def test_extracted_document_shape_fields() -> None:
    fetched = FetchedDocument(
        run_id="run-2",
        source_id="source-2",
        requested_url="https://example.com/minimal",
        final_url="https://example.com/minimal",
        status_code=200,
        content_type="text/html",
        raw_html=_fixture("minimal_page.html"),
        success=True,
    )
    extracted = Extractor().extract(fetched)
    assert str(extracted.source_url) == "https://example.com/minimal"
    assert str(extracted.final_url) == "https://example.com/minimal"
    assert extracted.domain == "example.com"
    assert extracted.raw_content


def test_extractor_handles_js_heavy_shell_as_empty() -> None:
    fetched = FetchedDocument(
        run_id="run-3",
        source_id="source-3",
        requested_url="https://example.com/app",
        final_url="https://example.com/app",
        status_code=200,
        content_type="text/html",
        raw_html=_fixture("js_heavy_minimal.html"),
        success=True,
    )
    extracted = Extractor().extract(fetched)
    assert extracted.title == "Script Heavy Shell"
    assert extracted.extraction_status in {ExtractionStatus.EMPTY, ExtractionStatus.SUCCESS}

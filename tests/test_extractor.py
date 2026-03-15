from src.data.models import FetchedDocument
from src.web.extractor import Extractor


def test_extractor_shape_from_html() -> None:
    fetched = FetchedDocument(
        run_id="run-1",
        source_id="source-1",
        requested_url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        content_type="text/html",
        raw_html="<html><head><title>Sample</title></head><body><main><p>Hello world content.</p></main></body></html>",
        success=True,
    )
    extracted = Extractor().extract(fetched)
    assert extracted.title == "Sample"
    assert "Hello" in extracted.content
    assert extracted.content_hash

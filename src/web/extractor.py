"""Content extraction for fetched web documents."""

from __future__ import annotations

import hashlib

import trafilatura
from selectolax.parser import HTMLParser

from src.data.models import ExtractedDocument, FetchedDocument
from src.web.cleaners import normalize_whitespace, trim_text


class Extractor:
    """Extracts clean text and metadata from fetched documents."""

    def extract(self, fetched: FetchedDocument) -> ExtractedDocument:
        """Extract normalized document content and metadata."""
        html = fetched.raw_html or fetched.text or ""

        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_recall=True,
        )

        title: str | None = None
        if html:
            tree = HTMLParser(html)
            title_node = tree.css_first("title")
            title = title_node.text(strip=True) if title_node else None

        content = normalize_whitespace(extracted or fetched.text or "")
        content = trim_text(content)

        return ExtractedDocument(
            run_id=fetched.run_id,
            source_id=fetched.source_id,
            title=title,
            content=content,
            metadata={
                "status_code": fetched.status_code,
                "content_type": fetched.content_type,
                "final_url": str(fetched.final_url) if fetched.final_url else None,
            },
            content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest() if content else None,
        )

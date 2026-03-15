"""Content extraction for fetched web documents."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from urllib.parse import urlparse

import trafilatura
from selectolax.parser import HTMLParser

from src.data.models import ExtractedDocument, ExtractionStatus, FetchedDocument
from src.web.cleaners import normalize_whitespace, remove_boilerplate_lines, trim_text


class Extractor:
    """Extracts clean text and metadata from fetched documents."""

    def extract(self, fetched: FetchedDocument) -> ExtractedDocument:
        """Extract normalized document content and metadata."""
        raw_source = fetched.raw_html or fetched.text or ""
        tree = HTMLParser(raw_source) if raw_source else None

        extracted_text = trafilatura.extract(
            raw_source,
            include_comments=False,
            include_tables=False,
            favor_recall=True,
        )

        title = self._extract_title(tree)
        canonical_url = self._meta_content(tree, 'link[rel="canonical"]', attr="href")
        meta_description = self._meta_content(tree, 'meta[name="description"]')
        publish_date = self._extract_publish_date(tree)

        cleaned = normalize_whitespace(extracted_text or fetched.text or "")
        cleaned = remove_boilerplate_lines(cleaned)
        cleaned = trim_text(cleaned)

        final_url = str(fetched.final_url) if fetched.final_url else None
        source_url = str(fetched.requested_url)
        status = ExtractionStatus.SUCCESS if cleaned else ExtractionStatus.EMPTY

        return ExtractedDocument(
            run_id=fetched.run_id,
            source_id=fetched.source_id,
            source_url=source_url,
            final_url=final_url,
            domain=urlparse(final_url or source_url).netloc.lower() or None,
            title=title,
            raw_content=trim_text(normalize_whitespace(raw_source), max_chars=4000) if raw_source else None,
            content=cleaned,
            metadata={
                "status_code": fetched.status_code,
                "content_type": fetched.content_type,
                "canonical_url": canonical_url,
                "meta_description": meta_description,
                "publish_date": publish_date,
                "fetched_at": fetched.fetched_at.isoformat(),
            },
            extraction_status=status,
            content_hash=hashlib.sha256(cleaned.encode("utf-8")).hexdigest() if cleaned else None,
            extracted_at=datetime.now(UTC),
        )

    def _extract_title(self, tree: HTMLParser | None) -> str | None:
        if tree is None:
            return None
        for selector in ("meta[property='og:title']", "title", "h1"):
            node = tree.css_first(selector)
            if node is None:
                continue
            if selector.startswith("meta"):
                title = node.attributes.get("content", "")
            else:
                title = node.text(strip=True)
            if title:
                return normalize_whitespace(title)
        return None

    def _meta_content(self, tree: HTMLParser | None, selector: str, attr: str = "content") -> str | None:
        if tree is None:
            return None
        node = tree.css_first(selector)
        if node is None:
            return None
        value = node.attributes.get(attr, "").strip()
        return value or None

    def _extract_publish_date(self, tree: HTMLParser | None) -> str | None:
        if tree is None:
            return None
        for selector, attr in (
            ("meta[property='article:published_time']", "content"),
            ("meta[name='pubdate']", "content"),
            ("time[datetime]", "datetime"),
        ):
            value = self._meta_content(tree, selector, attr=attr)
            if value:
                return value
        return None

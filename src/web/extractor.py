"""Content extraction for fetched web documents."""

from __future__ import annotations

import hashlib

import trafilatura
from selectolax.parser import HTMLParser

from src.data.models import ExtractedDocument, FetchedDocument
from src.web.cleaners import normalize_whitespace, remove_boilerplate_lines, trim_text


class Extractor:
    """Extracts clean text and metadata from fetched documents."""

    def _extract_title(self, tree: HTMLParser) -> str | None:
        og_title = tree.css_first("meta[property='og:title']")
        if og_title and og_title.attributes.get("content"):
            return og_title.attributes["content"].strip()

        title_node = tree.css_first("title")
        if title_node:
            return title_node.text(strip=True)

        h1 = tree.css_first("h1")
        return h1.text(strip=True) if h1 else None

    def extract(self, fetched: FetchedDocument) -> ExtractedDocument:
        """Extract normalized document content and metadata."""
        html = fetched.raw_html or fetched.text or ""

        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_recall=True,
            include_links=False,
        )

        title: str | None = None
        metadata: dict[str, str | int | bool | None] = {
            "status_code": fetched.status_code,
            "content_type": fetched.content_type,
            "final_url": str(fetched.final_url) if fetched.final_url else None,
            "fetch_method": fetched.fetch_method,
            "fetch_outcome": fetched.fetch_outcome,
            "fallback_triggered": fetched.fallback_triggered,
            "fallback_reason": fetched.fallback_reason,
            "rendered_content_available": fetched.rendered_content_available,
        }
        if html:
            tree = HTMLParser(html)
            title = self._extract_title(tree)
            canonical = tree.css_first("link[rel='canonical']")
            description = tree.css_first("meta[name='description']")
            author = tree.css_first("meta[name='author']")
            published_time = tree.css_first("meta[property='article:published_time']")
            metadata.update(
                {
                    "canonical_url": canonical.attributes.get("href") if canonical else None,
                    "description": description.attributes.get("content") if description else None,
                    "author": author.attributes.get("content") if author else None,
                    "published_time": published_time.attributes.get("content") if published_time else None,
                }
            )

        raw_content = extracted or fetched.text or ""
        content = remove_boilerplate_lines(raw_content)
        content = normalize_whitespace(content)
        content = trim_text(content)
        text_length = len(content)

        quality = "low"
        if text_length >= 1000:
            quality = "high"
        elif text_length >= 200:
            quality = "medium"

        return ExtractedDocument(
            run_id=fetched.run_id,
            source_id=fetched.source_id,
            title=title,
            content=content,
            metadata=metadata,
            extraction_quality=quality,
            text_length=text_length,
            content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest() if content else None,
        )

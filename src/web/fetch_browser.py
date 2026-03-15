"""Bounded browser-based fetch fallback."""

from __future__ import annotations

import asyncio

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from src.core.config import get_settings
from src.data.models import CandidateSource, FetchMethod, FetchOutcome, FetchedDocument


async def fetch_via_browser(source: CandidateSource) -> FetchedDocument:
    """Render one page with strict bounds for JS-heavy fallback recovery."""
    settings = get_settings()
    timeout_ms = int(settings.browser_fallback_timeout_seconds * 1000)

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=settings.user_agent)
            page = await context.new_page()

            response = await page.goto(str(source.url), wait_until="domcontentloaded", timeout=timeout_ms)
            await page.wait_for_timeout(int(settings.browser_fallback_wait_seconds * 1000))

            html = await page.content()
            title = await page.title()
            final_url = page.url
            status_code = response.status if response else None
            await context.close()
            await browser.close()

        success = bool(html and len(html.strip()) > 0)
        return FetchedDocument(
            run_id=source.run_id,
            source_id=source.id,
            requested_url=source.url,
            final_url=final_url,
            status_code=status_code,
            content_type="text/html",
            content_length=len(html.encode("utf-8")) if html else 0,
            text=title,
            raw_html=html,
            fetch_method=FetchMethod.BROWSER,
            fetch_outcome=FetchOutcome.SUCCESS if success else FetchOutcome.EMPTY_CONTENT,
            success=success,
            rendered_content_available=success,
            error=None if success else "browser_empty_content",
        )
    except PlaywrightTimeoutError:
        return FetchedDocument(
            run_id=source.run_id,
            source_id=source.id,
            requested_url=source.url,
            fetch_method=FetchMethod.BROWSER,
            fetch_outcome=FetchOutcome.TIMEOUT,
            success=False,
            rendered_content_available=False,
            error="browser_timeout",
        )
    except (PlaywrightError, OSError, asyncio.TimeoutError) as exc:
        return FetchedDocument(
            run_id=source.run_id,
            source_id=source.id,
            requested_url=source.url,
            fetch_method=FetchMethod.BROWSER,
            fetch_outcome=FetchOutcome.BROWSER_UNAVAILABLE,
            success=False,
            rendered_content_available=False,
            error=f"browser_failed:{exc}",
        )

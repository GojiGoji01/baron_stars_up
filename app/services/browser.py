from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from config import settings


logger = logging.getLogger(__name__)

try:
    from playwright.async_api import BrowserContext, Error as PlaywrightError, Page, Playwright, async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on installed deps
    BrowserContext = Any  # type: ignore[assignment]
    Page = Any  # type: ignore[assignment]
    Playwright = Any  # type: ignore[assignment]
    PlaywrightError = Exception
    async_playwright = None
    PLAYWRIGHT_AVAILABLE = False


class BrowserManagerError(RuntimeError):
    pass


class BrowserManager:
    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._lock = asyncio.Lock()
        self._pages: set[Page] = set()
        self._stopping = False

    async def start(self) -> None:
        if not settings.playwright_enabled:
            logger.info("playwright_disabled_by_config")
            return

        async with self._lock:
            if self._stopping:
                raise BrowserManagerError("Playwright is shutting down")

            if self._context is not None:
                logger.debug("playwright_context_already_started")
                return

            if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
                raise BrowserManagerError(
                    "Playwright is not installed. Install requirements and run "
                    "'playwright install chromium'."
                )

            userdata_dir = Path(settings.playwright_userdata_dir).resolve()
            userdata_dir.mkdir(parents=True, exist_ok=True)
            launch_args: list[str] = []
            if settings.playwright_no_sandbox:
                launch_args.append("--no-sandbox")

            try:
                logger.info("playwright_starting")
                self._playwright = await async_playwright().start()
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(userdata_dir),
                    headless=settings.playwright_headless,
                    args=launch_args,
                    viewport={"width": 1440, "height": 900},
                    timeout=settings.playwright_launch_timeout_ms,
                )
            except Exception as error:
                await self._cleanup_failed_start()
                logger.exception("playwright_start_failed")
                raise BrowserManagerError(f"Failed to start Playwright context: {error}") from error

            logger.info(
                "playwright_context_started headless=%s userdata_dir=%s no_sandbox=%s",
                settings.playwright_headless,
                userdata_dir,
                settings.playwright_no_sandbox,
            )

    async def stop(self) -> None:
        async with self._lock:
            if self._stopping:
                logger.debug("playwright_stop_already_in_progress")
                return

            self._stopping = True
            logger.info(
                "playwright_shutdown_started tracked_pages=%s context_started=%s",
                len(self._pages),
                self._context is not None,
            )
            try:
                await self._close_tracked_pages()

                if self._context is not None:
                    try:
                        await self._context.close()
                        logger.info("playwright_context_closed")
                    except Exception:
                        logger.exception("playwright_context_close_failed")
                    finally:
                        self._context = None

                if self._playwright is not None:
                    try:
                        await self._playwright.stop()
                        logger.info("playwright_driver_stopped")
                    except Exception:
                        logger.exception("playwright_driver_stop_failed")
                    finally:
                        self._playwright = None
            finally:
                self._pages.clear()
                self._stopping = False
                logger.info("playwright_shutdown_finished")

    async def new_page(self) -> Page:
        context = await self.get_context()
        page = await context.new_page()
        self._register_page(page)
        logger.info("playwright_page_created tracked_pages=%s", len(self._pages))
        return page

    async def get_page(self) -> Page:
        return await self.new_page()

    async def get_context(self) -> BrowserContext:
        if not settings.playwright_enabled:
            raise BrowserManagerError("Playwright is disabled by config")

        if self._context is None:
            await self.start()

        if self._context is None:
            raise BrowserManagerError("Playwright context is not available")

        return self._context

    def get_debug_info(self) -> dict[str, Any]:
        return {
            "playwright_enabled": settings.playwright_enabled,
            "playwright_available": PLAYWRIGHT_AVAILABLE,
            "playwright_context_started": self._context is not None,
            "playwright_tracked_pages": len(self._pages),
            "playwright_headless": settings.playwright_headless,
            "playwright_userdata_dir": str(Path(settings.playwright_userdata_dir).resolve()),
            "playwright_no_sandbox": settings.playwright_no_sandbox,
        }

    async def _cleanup_failed_start(self) -> None:
        await self._close_tracked_pages()
        if self._context is not None:
            await self._context.close()
            self._context = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    def _register_page(self, page: Page) -> None:
        self._pages.add(page)
        page.on("close", lambda: self._discard_page(page))

    def _discard_page(self, page: Page) -> None:
        self._pages.discard(page)

    async def _close_tracked_pages(self) -> None:
        if not self._pages:
            return

        pages = list(self._pages)
        for page in pages:
            try:
                if not page.is_closed():
                    await page.close()
            except Exception:
                logger.exception("playwright_page_close_failed")
            finally:
                self._pages.discard(page)
        logger.info("playwright_pages_closed")


browser_manager = BrowserManager()


def get_browser_manager() -> BrowserManager:
    return browser_manager

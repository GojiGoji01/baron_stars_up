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

    async def start(self) -> None:
        if not settings.playwright_enabled:
            logger.info("playwright_disabled_by_config")
            return

        async with self._lock:
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
            if self._context is not None:
                await self._context.close()
                self._context = None

            if self._playwright is not None:
                await self._playwright.stop()
                self._playwright = None

            logger.info("playwright_context_stopped")

    async def new_page(self) -> Page:
        context = await self.get_context()
        return await context.new_page()

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
            "playwright_headless": settings.playwright_headless,
            "playwright_userdata_dir": str(Path(settings.playwright_userdata_dir).resolve()),
            "playwright_no_sandbox": settings.playwright_no_sandbox,
        }

    async def _cleanup_failed_start(self) -> None:
        if self._context is not None:
            await self._context.close()
            self._context = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None


browser_manager = BrowserManager()


def get_browser_manager() -> BrowserManager:
    return browser_manager

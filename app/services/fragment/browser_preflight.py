from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.browser import BrowserManagerError, get_browser_manager
from app.services.fragment.browser_session import FragmentBrowserSessionService
from app.services.fragment.browser_state import collect_fragment_page_state
from app.services.fragment.browser_warmup import FragmentBrowserWarmupService
from config import settings


logger = logging.getLogger(__name__)


class FragmentBrowserPreflightService:
    def __init__(
        self,
        *,
        cookies_base64: str | None = None,
        local_storage_base64: str | None = None,
    ) -> None:
        self.cookies_base64 = cookies_base64
        self.local_storage_base64 = local_storage_base64

    async def collect_preflight_info(self, *, sync_session: bool = True) -> dict[str, Any]:
        browser = get_browser_manager()
        page = await browser.new_page()
        screenshot_path = self._build_screenshot_path()
        session_sync_info: dict[str, Any] | None = None
        warmup_info: dict[str, Any] | None = None

        try:
            if sync_session:
                session_sync_info = await FragmentBrowserSessionService().sync_from_config_safe_with_state(
                    cookies_base64=self.cookies_base64,
                    local_storage_base64=self.local_storage_base64,
                )
                warmup_info = await FragmentBrowserWarmupService(
                    cookies_base64=self.cookies_base64,
                    local_storage_base64=self.local_storage_base64,
                ).warmup_session_safe()

            await page.goto(
                settings.fragment_web_base_url,
                wait_until="domcontentloaded",
                timeout=settings.fragment_browser_timeout_ms,
            )
            await page.wait_for_timeout(1500)
            page_state = await collect_fragment_page_state(page)
            await page.screenshot(path=str(screenshot_path), full_page=True)

            return {
                "fragment_preflight_ok": True,
                "fragment_session_sync": session_sync_info,
                "fragment_warmup": warmup_info,
                "fragment_screenshot_path": str(screenshot_path),
                **page_state,
            }
        except Exception as error:
            logger.exception("fragment_browser_preflight_failed")
            return {
                "fragment_preflight_ok": False,
                "fragment_browser_preflight_error": str(error),
                "fragment_session_sync": session_sync_info,
                "fragment_warmup": warmup_info,
                "fragment_screenshot_path": str(screenshot_path),
            }
        finally:
            await page.close()

    async def collect_safe_preflight_info(self, *, sync_session: bool = True) -> dict[str, Any]:
        try:
            return await self.collect_preflight_info(sync_session=sync_session)
        except BrowserManagerError as error:
            return {
                "fragment_preflight_ok": False,
                "fragment_browser_preflight_error": str(error),
            }

    def _build_screenshot_path(self) -> Path:
        directory = Path(settings.fragment_browser_screenshots_dir).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return directory / f"fragment_preflight_{timestamp}.png"

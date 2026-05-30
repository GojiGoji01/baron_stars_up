from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.browser import BrowserManagerError, get_browser_manager
from config import settings


logger = logging.getLogger(__name__)


class FragmentBrowserDebugService:
    async def collect_session_debug_info(self) -> dict[str, Any]:
        browser = get_browser_manager()
        page = await browser.new_page()
        screenshot_path = self._build_screenshot_path()

        try:
            await page.goto(
                settings.fragment_web_base_url,
                wait_until="domcontentloaded",
                timeout=settings.fragment_browser_timeout_ms,
            )
            await page.wait_for_timeout(1500)

            title = await page.title()
            local_storage_keys = await page.evaluate(
                """
                () => Array.from({ length: localStorage.length }, (_, i) => localStorage.key(i))
                """
            )
            session_storage_keys = await page.evaluate(
                """
                () => Array.from({ length: sessionStorage.length }, (_, i) => sessionStorage.key(i))
                """
            )
            connect_wallet_visible = await page.locator("text=Connect wallet").count() > 0
            body_text = await page.locator("body").inner_text()
            await page.screenshot(path=str(screenshot_path), full_page=True)

            return {
                "fragment_url": page.url,
                "fragment_title": title,
                "fragment_connect_wallet_visible": connect_wallet_visible,
                "fragment_local_storage_keys": local_storage_keys,
                "fragment_session_storage_keys": session_storage_keys,
                "fragment_body_excerpt": body_text[:1000],
                "fragment_screenshot_path": str(screenshot_path),
            }
        except Exception as error:
            logger.exception("fragment_browser_debug_failed")
            return {
                "fragment_browser_debug_error": str(error),
                "fragment_screenshot_path": str(screenshot_path),
            }
        finally:
            await page.close()

    async def collect_safe_debug_info(self) -> dict[str, Any]:
        try:
            return await self.collect_session_debug_info()
        except BrowserManagerError as error:
            return {"fragment_browser_debug_error": str(error)}

    def _build_screenshot_path(self) -> Path:
        directory = Path(settings.fragment_browser_screenshots_dir).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return directory / f"fragment_debug_{timestamp}.png"

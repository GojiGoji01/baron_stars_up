from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.browser import BrowserManagerError, get_browser_manager
from app.services.fragment.browser_session import FragmentBrowserSessionService
from app.services.fragment.browser_warmup import FragmentBrowserWarmupService
from config import settings


logger = logging.getLogger(__name__)


class FragmentBrowserPreflightService:
    async def collect_preflight_info(self, *, sync_session: bool = True) -> dict[str, Any]:
        browser = get_browser_manager()
        page = await browser.new_page()
        screenshot_path = self._build_screenshot_path()
        session_sync_info: dict[str, Any] | None = None
        warmup_info: dict[str, Any] | None = None

        try:
            if sync_session:
                session_sync_info = await FragmentBrowserSessionService().sync_from_config_safe()
                warmup_info = await FragmentBrowserWarmupService().warmup_session_safe()

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
            ton_connect_keys = [key for key in local_storage_keys if str(key).startswith("ton-connect")]
            body_text = await page.locator("body").inner_text()
            await page.screenshot(path=str(screenshot_path), full_page=True)

            wallet_session_ready = bool(ton_connect_keys) and not connect_wallet_visible

            return {
                "fragment_preflight_ok": True,
                "fragment_session_sync": session_sync_info,
                "fragment_warmup": warmup_info,
                "fragment_url": page.url,
                "fragment_title": title,
                "fragment_connect_wallet_visible": connect_wallet_visible,
                "fragment_local_storage_key_count": len(local_storage_keys),
                "fragment_session_storage_key_count": len(session_storage_keys),
                "fragment_ton_connect_key_count": len(ton_connect_keys),
                "fragment_wallet_session_ready": wallet_session_ready,
                "fragment_body_excerpt": body_text[:600],
                "fragment_screenshot_path": str(screenshot_path),
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

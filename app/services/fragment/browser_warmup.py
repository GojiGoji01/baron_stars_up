from __future__ import annotations

import logging
from typing import Any

from app.services.browser import BrowserManagerError, get_browser_manager
from app.services.fragment.browser_session import FragmentBrowserSessionService
from config import settings


logger = logging.getLogger(__name__)


class FragmentBrowserWarmupService:
    async def warmup_session(self) -> dict[str, Any]:
        browser = get_browser_manager()
        page = await browser.new_page()

        try:
            session_sync = await FragmentBrowserSessionService().sync_from_config_safe()
            attempts: list[dict[str, Any]] = []

            for attempt_index in range(1, 4):
                await page.goto(
                    settings.fragment_web_base_url,
                    wait_until="domcontentloaded",
                    timeout=settings.fragment_browser_timeout_ms,
                )
                await page.wait_for_timeout(1500)

                local_storage_keys = await page.evaluate(
                    """
                    () => Array.from({ length: localStorage.length }, (_, i) => localStorage.key(i))
                    """
                )
                connect_wallet_visible = await page.locator("text=Connect wallet").count() > 0
                ton_connect_key_count = len(
                    [key for key in local_storage_keys if str(key).startswith("ton-connect")]
                )
                wallet_session_ready = ton_connect_key_count > 0 and not connect_wallet_visible

                attempt_info = {
                    "attempt": attempt_index,
                    "fragment_url": page.url,
                    "connect_wallet_visible": connect_wallet_visible,
                    "ton_connect_key_count": ton_connect_key_count,
                    "wallet_session_ready": wallet_session_ready,
                }
                attempts.append(attempt_info)

                if wallet_session_ready:
                    return {
                        "fragment_warmup_ok": True,
                        "fragment_warmup_attempts": attempts,
                        "fragment_session_sync": session_sync,
                        "fragment_wallet_session_ready": True,
                    }

                if ton_connect_key_count > 0:
                    await page.reload(
                        wait_until="domcontentloaded",
                        timeout=settings.fragment_browser_timeout_ms,
                    )
                else:
                    await page.wait_for_timeout(1000)

            return {
                "fragment_warmup_ok": False,
                "fragment_warmup_attempts": attempts,
                "fragment_session_sync": session_sync,
                "fragment_wallet_session_ready": False,
            }
        except Exception as error:
            logger.exception("fragment_browser_warmup_failed")
            return {
                "fragment_warmup_ok": False,
                "fragment_wallet_session_ready": False,
                "fragment_browser_warmup_error": str(error),
            }
        finally:
            await page.close()

    async def warmup_session_safe(self) -> dict[str, Any]:
        try:
            return await self.warmup_session()
        except BrowserManagerError as error:
            return {
                "fragment_warmup_ok": False,
                "fragment_wallet_session_ready": False,
                "fragment_browser_warmup_error": str(error),
            }

from __future__ import annotations

import logging
from typing import Any

from app.services.browser import BrowserManagerError, get_browser_manager
from app.services.fragment.browser_session import FragmentBrowserSessionService
from app.services.fragment.browser_state import collect_fragment_page_state
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
                page_state = await collect_fragment_page_state(page)

                attempt_info = {
                    "attempt": attempt_index,
                    "fragment_url": page_state["fragment_url"],
                    "connect_wallet_visible": page_state["fragment_connect_wallet_visible"],
                    "connect_ton_visible": page_state["fragment_connect_ton_visible"],
                    "connect_cta_visible": page_state["fragment_connect_cta_visible"],
                    "ton_connect_key_count": page_state["fragment_ton_connect_key_count"],
                    "wallet_session_ready": page_state["fragment_wallet_session_ready"],
                }
                attempts.append(attempt_info)

                if page_state["fragment_wallet_session_ready"]:
                    return {
                        "fragment_warmup_ok": True,
                        "fragment_warmup_attempts": attempts,
                        "fragment_session_sync": session_sync,
                        "fragment_wallet_session_ready": True,
                    }

                if page_state["fragment_ton_connect_key_count"] > 0:
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

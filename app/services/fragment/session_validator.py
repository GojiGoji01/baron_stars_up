from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.browser import BrowserManagerError, get_browser_manager
from app.services.fragment.browser_session import FragmentBrowserSessionService
from app.services.fragment.browser_state import collect_fragment_page_state
from config import settings


logger = logging.getLogger(__name__)


class FragmentSessionValidatorService:
    async def validate(self) -> dict[str, Any]:
        browser = get_browser_manager()
        page = await browser.new_page()
        screenshot_path = self._build_screenshot_path()
        session_service = FragmentBrowserSessionService()
        session_sync: dict[str, Any] | None = None

        try:
            if session_service.should_sync_from_state():
                session_sync = await session_service.sync_from_config_safe()
            else:
                session_sync = session_service.build_skip_sync_result()

            await page.goto(
                f"{settings.fragment_web_base_url.rstrip('/')}/stars/buy?amount=50",
                wait_until="domcontentloaded",
                timeout=settings.fragment_browser_timeout_ms,
            )
            await page.wait_for_timeout(1500)

            page_state = await collect_fragment_page_state(page)
            buy_state = await self._collect_buy_button_state(page)
            is_logged_in = bool(buy_state["buy_button_found"]) and not bool(page_state["fragment_connect_cta_visible"])
            buy_button_available = bool(buy_state["buy_button_found"]) and not bool(buy_state["buy_button_disabled"])

            await page.screenshot(path=str(screenshot_path), full_page=True)

            return {
                "fragment_session_valid": is_logged_in,
                "fragment_login_required": not is_logged_in,
                "fragment_buy_button_available": buy_button_available,
                "fragment_session_sync": session_sync,
                "fragment_browser_mode": "production" if settings.playwright_headless else "warmup",
                "fragment_session_screenshot_path": str(screenshot_path),
                **page_state,
                **buy_state,
            }
        except Exception as error:
            logger.exception("fragment_session_validation_failed")
            return {
                "fragment_session_valid": False,
                "fragment_login_required": True,
                "fragment_buy_button_available": False,
                "fragment_browser_mode": "production" if settings.playwright_headless else "warmup",
                "fragment_session_validation_error": str(error),
                "fragment_session_sync": session_sync,
                "fragment_session_screenshot_path": str(screenshot_path),
            }
        finally:
            await page.close()

    async def validate_safe(self) -> dict[str, Any]:
        try:
            return await self.validate()
        except BrowserManagerError as error:
            return {
                "fragment_session_valid": False,
                "fragment_login_required": True,
                "fragment_buy_button_available": False,
                "fragment_browser_mode": "production" if settings.playwright_headless else "warmup",
                "fragment_session_validation_error": str(error),
            }

    async def _collect_buy_button_state(self, page: Any) -> dict[str, Any]:
        candidates = [
            page.locator("button:has-text('Buy')").first,
            page.locator("[role='button']:has-text('Buy')").first,
            page.locator("text=Buy").first,
        ]
        for locator in candidates:
            try:
                if await locator.count() == 0:
                    continue
                text = await locator.text_content()
                is_disabled = await locator.is_disabled()
                aria_disabled = await locator.get_attribute("aria-disabled")
                return {
                    "buy_button_found": True,
                    "buy_button_text": text,
                    "buy_button_disabled": is_disabled,
                    "buy_button_aria_disabled": aria_disabled,
                }
            except Exception:
                continue

        return {
            "buy_button_found": False,
            "buy_button_text": None,
            "buy_button_disabled": None,
            "buy_button_aria_disabled": None,
        }

    def _build_screenshot_path(self) -> Path:
        directory = Path(settings.fragment_browser_screenshots_dir).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return directory / f"fragment_session_validation_{timestamp}.png"

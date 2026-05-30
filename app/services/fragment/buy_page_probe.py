from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.services.browser import BrowserManagerError, get_browser_manager
from app.services.fragment.browser_session import FragmentBrowserSessionService
from app.services.fragment.browser_state import collect_fragment_page_state
from app.services.fragment.browser_warmup import FragmentBrowserWarmupService
from config import settings


logger = logging.getLogger(__name__)


class FragmentBuyPageProbeService:
    async def probe(self, *, username: str, amount: int | None = None) -> dict[str, Any]:
        normalized_username = username.strip()
        if not normalized_username:
            raise ValueError("username is required")
        if not normalized_username.startswith("@"):
            normalized_username = f"@{normalized_username}"

        browser = get_browser_manager()
        page = await browser.new_page()
        screenshot_path = self._build_screenshot_path(normalized_username)

        try:
            session_sync = await FragmentBrowserSessionService().sync_from_config_safe()
            warmup = await FragmentBrowserWarmupService().warmup_session_safe()
            routes = self._build_candidate_routes(normalized_username, amount)
            attempts: list[dict[str, Any]] = []

            for route in routes:
                try:
                    await page.goto(
                        route,
                        wait_until="domcontentloaded",
                        timeout=settings.fragment_browser_timeout_ms,
                    )
                    await page.wait_for_timeout(1500)
                except Exception as error:
                    attempts.append(
                        {
                            "candidate_url": route,
                            "open_ok": False,
                            "error": str(error),
                        }
                    )
                    continue

                page_state = await collect_fragment_page_state(page)
                buy_state = await self._collect_buy_button_state(page)
                next_step_state = None
                if buy_state["buy_button_found"] and self._is_package_cta(buy_state["buy_button_text"]):
                    next_step_state = await self._probe_after_package_cta_click(page)
                attempt = {
                    "candidate_url": route,
                    "open_ok": True,
                    **page_state,
                    **buy_state,
                    "next_step_probe": next_step_state,
                }
                attempts.append(attempt)

                if buy_state["buy_button_found"]:
                    break

            await page.screenshot(path=str(screenshot_path), full_page=True)

            matched_attempt = next(
                (attempt for attempt in attempts if attempt.get("buy_button_found")),
                attempts[-1] if attempts else None,
            )

            return {
                "fragment_buy_probe_ok": True,
                "fragment_buy_probe_username": normalized_username,
                "fragment_buy_probe_amount": amount,
                "fragment_session_sync": session_sync,
                "fragment_warmup": warmup,
                "fragment_buy_probe_attempts": attempts,
                "fragment_buy_probe_match": matched_attempt,
                "fragment_buy_probe_screenshot_path": str(screenshot_path),
            }
        except Exception as error:
            logger.exception("fragment_buy_page_probe_failed")
            return {
                "fragment_buy_probe_ok": False,
                "fragment_buy_probe_username": normalized_username,
                "fragment_buy_probe_amount": amount,
                "fragment_buy_probe_error": str(error),
                "fragment_buy_probe_screenshot_path": str(screenshot_path),
            }
        finally:
            await page.close()

    async def probe_safe(self, *, username: str, amount: int | None = None) -> dict[str, Any]:
        try:
            return await self.probe(username=username, amount=amount)
        except BrowserManagerError as error:
            return {
                "fragment_buy_probe_ok": False,
                "fragment_buy_probe_username": username,
                "fragment_buy_probe_amount": amount,
                "fragment_buy_probe_error": str(error),
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

    async def _probe_after_package_cta_click(self, page: Any) -> dict[str, Any]:
        try:
            cta = page.locator("button:has-text('Buy Stars Package')").first
            if await cta.count() == 0:
                cta = page.locator("[role='button']:has-text('Buy Stars Package')").first
            if await cta.count() == 0:
                cta = page.locator("text=Buy Stars Package").first
            if await cta.count() == 0:
                return {"next_step_open_ok": False, "error": "package_cta_not_found"}

            await cta.click(timeout=settings.fragment_browser_timeout_ms)
            await page.wait_for_timeout(1500)

            page_state = await collect_fragment_page_state(page)
            buy_state = await self._collect_buy_button_state(page)
            return {
                "next_step_open_ok": True,
                **page_state,
                **buy_state,
            }
        except Exception as error:
            return {
                "next_step_open_ok": False,
                "error": str(error),
            }

    def _is_package_cta(self, button_text: str | None) -> bool:
        return (button_text or "").strip().lower() == "buy stars package"

    def _build_candidate_routes(self, username: str, amount: int | None) -> list[str]:
        clean_username = username.lstrip("@")
        encoded_username = quote(clean_username)
        routes = [
            f"{settings.fragment_web_base_url.rstrip('/')}/stars",
            f"{settings.fragment_web_base_url.rstrip('/')}/stars/{encoded_username}",
            f"{settings.fragment_web_base_url.rstrip('/')}/stars/buy/{encoded_username}",
            f"{settings.fragment_web_base_url.rstrip('/')}/gifts/stars/{encoded_username}",
        ]
        if amount is not None:
            routes.extend(
                [
                    f"{settings.fragment_web_base_url.rstrip('/')}/stars/{encoded_username}?amount={amount}",
                    f"{settings.fragment_web_base_url.rstrip('/')}/stars/buy/{encoded_username}?amount={amount}",
                ]
            )
        # preserve order but remove duplicates
        return list(dict.fromkeys(routes))

    def _build_screenshot_path(self, username: str) -> Path:
        directory = Path(settings.fragment_browser_screenshots_dir).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_username = username.lstrip("@").replace("/", "_")
        return directory / f"fragment_buy_probe_{safe_username}_{timestamp}.png"

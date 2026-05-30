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


class FragmentConnectTonService:
    def __init__(
        self,
        *,
        cookies_base64: str | None = None,
        local_storage_base64: str | None = None,
    ) -> None:
        self.cookies_base64 = cookies_base64
        self.local_storage_base64 = local_storage_base64

    async def connect(self, *, amount: int | None = None) -> dict[str, Any]:
        browser = get_browser_manager()
        page = await browser.new_page()
        screenshot_path = self._build_screenshot_path()
        session_service = FragmentBrowserSessionService()

        try:
            sync_info = await session_service.sync_from_config_safe_with_state(
                cookies_base64=self.cookies_base64,
                local_storage_base64=self.local_storage_base64,
            )
            await page.goto(
                self._build_buy_url(amount),
                wait_until="domcontentloaded",
                timeout=settings.fragment_browser_timeout_ms,
            )
            await page.wait_for_timeout(1500)

            before_state = await collect_fragment_page_state(page)
            buy_state_before = await self._collect_buy_button_state(page)
            connect_button_info = await self._collect_connect_button_info(page)

            connect_action = {
                "connect_clicked": False,
                "modal_opened": False,
                "preferred_wallet_clicked": False,
                "preferred_wallet_name": None,
            }

            if connect_button_info["connect_button_found"]:
                await connect_button_info["locator"].click(timeout=settings.fragment_browser_timeout_ms)
                connect_action["connect_clicked"] = True
                await page.wait_for_timeout(1500)
                modal_state = await self._collect_modal_state(page)
                connect_action["modal_opened"] = modal_state["modal_visible"]

                preferred_wallet_name = self._extract_preferred_wallet_name(self.local_storage_base64)
                if preferred_wallet_name:
                    wallet_clicked = await self._click_wallet_option(page, preferred_wallet_name)
                    connect_action["preferred_wallet_clicked"] = wallet_clicked
                    connect_action["preferred_wallet_name"] = preferred_wallet_name
                    if wallet_clicked:
                        await page.wait_for_timeout(2000)
            else:
                modal_state = {"modal_visible": False, "wallet_options": []}

            after_state = await collect_fragment_page_state(page)
            buy_state_after = await self._collect_buy_button_state(page)
            exported_state = await session_service.export_session_state(page)

            await page.screenshot(path=str(screenshot_path), full_page=True)

            return {
                "fragment_connect_ton_ok": True,
                "fragment_connect_sync": sync_info,
                "fragment_connect_before": {**before_state, **buy_state_before},
                "fragment_connect_button": {
                    "found": connect_button_info["connect_button_found"],
                    "text": connect_button_info["connect_button_text"],
                },
                "fragment_connect_action": connect_action,
                "fragment_connect_modal": modal_state,
                "fragment_connect_after": {**after_state, **buy_state_after},
                "fragment_connect_export": {
                    "cookie_count": exported_state["cookie_count"],
                    "local_storage_item_count": exported_state["local_storage_item_count"],
                },
                "fragment_connect_cookies_base64": exported_state["cookies_base64"],
                "fragment_connect_local_storage_base64": exported_state["local_storage_base64"],
                "fragment_connect_screenshot_path": str(screenshot_path),
            }
        except Exception as error:
            logger.exception("fragment_connect_ton_failed")
            return {
                "fragment_connect_ton_ok": False,
                "fragment_connect_error": str(error),
                "fragment_connect_screenshot_path": str(screenshot_path),
            }
        finally:
            await page.close()

    async def connect_safe(self, *, amount: int | None = None) -> dict[str, Any]:
        try:
            return await self.connect(amount=amount)
        except BrowserManagerError as error:
            return {
                "fragment_connect_ton_ok": False,
                "fragment_connect_error": str(error),
            }

    def _build_buy_url(self, amount: int | None) -> str:
        base_url = f"{settings.fragment_web_base_url.rstrip('/')}/stars/buy"
        if amount is None:
            return base_url
        return f"{base_url}?amount={amount}"

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

    async def _collect_connect_button_info(self, page: Any) -> dict[str, Any]:
        candidates = [
            page.locator("button:has-text('Connect TON')").first,
            page.locator("[role='button']:has-text('Connect TON')").first,
            page.locator("text=Connect TON").first,
        ]
        for locator in candidates:
            try:
                if await locator.count() == 0:
                    continue
                return {
                    "connect_button_found": True,
                    "connect_button_text": await locator.text_content(),
                    "locator": locator,
                }
            except Exception:
                continue
        return {
            "connect_button_found": False,
            "connect_button_text": None,
            "locator": None,
        }

    async def _collect_modal_state(self, page: Any) -> dict[str, Any]:
        modal_text = ""
        wallet_options: list[str] = []
        modal_visible = False

        modal_candidates = [
            page.locator("[role='dialog']").first,
            page.locator("div[aria-modal='true']").first,
        ]
        for locator in modal_candidates:
            try:
                if await locator.count() == 0:
                    continue
                modal_visible = True
                modal_text = await locator.inner_text()
                button_locator = locator.locator("button")
                count = await button_locator.count()
                for index in range(min(count, 12)):
                    text = await button_locator.nth(index).text_content()
                    if text and text.strip():
                        wallet_options.append(text.strip())
                break
            except Exception:
                continue

        if not modal_visible:
            body_text = await page.locator("body").inner_text()
            if "tonkeeper" in body_text.lower() or "wallet" in body_text.lower():
                wallet_options = [line.strip() for line in body_text.splitlines() if line.strip()][:20]

        return {
            "modal_visible": modal_visible,
            "modal_text_excerpt": modal_text[:400],
            "wallet_options": wallet_options[:12],
        }

    async def _click_wallet_option(self, page: Any, wallet_name: str) -> bool:
        candidates = [
            page.locator(f"button:has-text('{wallet_name}')").first,
            page.locator(f"text={wallet_name}").first,
        ]
        for locator in candidates:
            try:
                if await locator.count() == 0:
                    continue
                await locator.click(timeout=settings.fragment_browser_timeout_ms)
                return True
            except Exception:
                continue
        return False

    def _extract_preferred_wallet_name(self, local_storage_base64: str | None) -> str | None:
        raw_value = (local_storage_base64 or "").strip()
        if not raw_value:
            return None
        try:
            import base64
            import json

            decoded = base64.b64decode(raw_value).decode("utf-8")
            payload = json.loads(decoded)
            if not isinstance(payload, dict):
                return None
            preferred = payload.get("ton-connect-ui_preferred-wallet")
            if isinstance(preferred, str) and preferred.strip():
                return preferred.strip()
            wallet_info = payload.get("ton-connect-ui_wallet-info")
            if isinstance(wallet_info, str) and wallet_info.strip().startswith("{"):
                parsed = json.loads(wallet_info)
                if isinstance(parsed, dict):
                    name = parsed.get("name")
                    if isinstance(name, str) and name.strip():
                        return name.strip()
        except Exception:
            return None
        return None

    def _build_screenshot_path(self) -> Path:
        directory = Path(settings.fragment_browser_screenshots_dir).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return directory / f"fragment_connect_ton_{timestamp}.png"

from __future__ import annotations

import base64
import json
import logging
from typing import Any

from app.services.browser import BrowserManagerError, get_browser_manager
from config import settings


logger = logging.getLogger(__name__)


class FragmentBrowserSessionService:
    async def sync_from_config(self) -> dict[str, Any]:
        browser = get_browser_manager()
        context = await browser.get_context()
        page = await browser.new_page()

        try:
            cookies_payload = self._decode_json_object(settings.fragment_cookies_base64)
            cookie_entries = self._build_cookie_entries(cookies_payload)
            if cookie_entries:
                await context.add_cookies(cookie_entries)

            await page.goto(
                settings.fragment_web_base_url,
                wait_until="domcontentloaded",
                timeout=settings.fragment_browser_timeout_ms,
            )

            local_storage_payload = self._decode_json_object(settings.fragment_local_storage_base64)
            local_storage_items = self._build_storage_items(local_storage_payload)
            if local_storage_items:
                await page.evaluate(
                    """
                    (entries) => {
                        for (const [key, value] of entries) {
                            localStorage.setItem(key, value);
                        }
                    }
                    """,
                    local_storage_items,
                )
                await page.reload(
                    wait_until="domcontentloaded",
                    timeout=settings.fragment_browser_timeout_ms,
                )

            await page.wait_for_timeout(1000)

            return {
                "fragment_browser_session_sync_ok": True,
                "fragment_cookie_count": len(cookie_entries),
                "fragment_local_storage_item_count": len(local_storage_items),
                "fragment_browser_session_url": page.url,
            }
        except Exception as error:
            logger.exception("fragment_browser_session_sync_failed")
            return {
                "fragment_browser_session_sync_ok": False,
                "fragment_browser_session_sync_error": str(error),
            }
        finally:
            await page.close()

    async def sync_from_config_safe(self) -> dict[str, Any]:
        try:
            return await self.sync_from_config()
        except BrowserManagerError as error:
            return {
                "fragment_browser_session_sync_ok": False,
                "fragment_browser_session_sync_error": str(error),
            }

    async def export_session_state(self, page: Any) -> dict[str, Any]:
        browser = get_browser_manager()
        context = await browser.get_context()
        cookies = await context.cookies([settings.fragment_web_base_url])
        local_storage = await page.evaluate(
            """
            () => Object.fromEntries(
                Array.from({ length: localStorage.length }, (_, i) => {
                    const key = localStorage.key(i);
                    return [key, localStorage.getItem(key)];
                })
            )
            """
        )
        return {
            "cookies_base64": self._encode_json_object({"cookies": cookies}),
            "local_storage_base64": self._encode_json_object(local_storage),
            "cookie_count": len(cookies),
            "local_storage_item_count": len(local_storage),
        }

    async def export_session_state_safe(self, page: Any) -> dict[str, Any]:
        try:
            return await self.export_session_state(page)
        except BrowserManagerError as error:
            return {
                "export_ok": False,
                "error": str(error),
            }

    def _decode_json_object(self, base64_value: str) -> dict[str, Any]:
        raw_value = (base64_value or "").strip()
        if not raw_value:
            return {}

        decoded = base64.b64decode(raw_value).decode("utf-8")
        parsed = json.loads(decoded)
        if not isinstance(parsed, dict):
            raise ValueError("Decoded Fragment session payload must be a JSON object")
        return parsed

    def _encode_json_object(self, payload: dict[str, Any]) -> str:
        return base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("utf-8")

    def _build_cookie_entries(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if not payload:
            return []

        entries: list[dict[str, Any]] = []
        raw_entries: Any = payload.get("cookies", payload)

        if isinstance(raw_entries, list):
            for item in raw_entries:
                if isinstance(item, dict):
                    normalized = self._normalize_cookie_dict(item)
                    if normalized:
                        entries.append(normalized)
            return entries

        if isinstance(raw_entries, dict):
            for key, value in raw_entries.items():
                if isinstance(value, dict):
                    merged = {"name": key, **value}
                    normalized = self._normalize_cookie_dict(merged)
                else:
                    normalized = self._normalize_cookie_dict({"name": key, "value": str(value)})
                if normalized:
                    entries.append(normalized)

        return entries

    def _normalize_cookie_dict(self, cookie: dict[str, Any]) -> dict[str, Any] | None:
        name = str(cookie.get("name") or "").strip()
        value = str(cookie.get("value") or "")
        if not name:
            return None

        normalized: dict[str, Any] = {
            "name": name,
            "value": value,
            "domain": str(cookie.get("domain") or ".fragment.com"),
            "path": str(cookie.get("path") or "/"),
            "httpOnly": bool(cookie.get("httpOnly", False)),
            "secure": bool(cookie.get("secure", True)),
        }

        expires = cookie.get("expires")
        if expires not in (None, ""):
            try:
                normalized["expires"] = float(expires)
            except (TypeError, ValueError):
                pass

        same_site = cookie.get("sameSite")
        if same_site:
            same_site_value = str(same_site).lower()
            normalized["sameSite"] = {
                "lax": "Lax",
                "strict": "Strict",
                "none": "None",
            }.get(same_site_value, "Lax")

        return normalized

    def _build_storage_items(self, payload: dict[str, Any]) -> list[list[str]]:
        if not payload:
            return []

        entries: list[list[str]] = []
        for key, value in payload.items():
            entries.append([str(key), str(value)])
        return entries

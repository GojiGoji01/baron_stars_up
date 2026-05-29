from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
from typing import Any

from app.services.fragment.base import (
    FragmentDeliveryResult,
    FragmentDeliveryStatus,
    FragmentError,
)
from config import settings


logger = logging.getLogger(__name__)

try:
    from fragment_api import FragmentAPIClient
    from fragment_api import FragmentAPIError as LibraryFragmentAPIError

    FRAGMENT_LIBRARY_AVAILABLE = True
except ImportError:
    FragmentAPIClient = None
    LibraryFragmentAPIError = Exception
    FRAGMENT_LIBRARY_AVAILABLE = False


class FragmentAPIError(FragmentError):
    """Raised when the Fragment API client cannot complete an operation."""


def _value(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


class FragmentAPIService:
    """Thin async adapter for the synchronous bbbuilt/fragment-stars-api client."""

    def __init__(
        self,
        *,
        wallet_mnemonic: str,
        api_url: str,
        api_mode: str,
        cookies_base64: str | None,
    ) -> None:
        self.wallet_mnemonic_base64 = self._as_base64_seed(wallet_mnemonic)
        self.api_url = api_url
        self.api_mode = api_mode
        self.cookies_base64 = self._validated_cookies(cookies_base64) if api_mode == "kyc" else None
        self.client = FragmentAPIClient(base_url=api_url) if FRAGMENT_LIBRARY_AVAILABLE else None

        if not FRAGMENT_LIBRARY_AVAILABLE:
            logger.error(
                "fragment_sdk_missing repository=%s",
                "https://github.com/bbbuilt/fragment-stars-api",
            )
        elif api_mode == "kyc" and self.cookies_base64:
            logger.info("fragment_api_mode mode=kyc cookies_configured=true")
        elif api_mode == "kyc":
            logger.warning("fragment_api_mode mode=kyc cookies_configured=false")
        else:
            logger.warning("fragment_api_mode mode=no_kyc")

    @staticmethod
    def _as_base64_seed(seed: str) -> str:
        seed = (seed or "").strip()
        if not seed:
            raise FragmentAPIError("FRAGMENT_WALLET_MNEMONIC is empty")

        try:
            decoded = base64.b64decode(seed).decode("utf-8")
            if len(decoded.split()) == 24:
                return seed
        except Exception:
            pass

        return base64.b64encode(seed.encode("utf-8")).decode("utf-8")

    @staticmethod
    def _validated_cookies(cookies_base64: str | None) -> str | None:
        if not cookies_base64:
            return None

        try:
            decoded = base64.b64decode(cookies_base64).decode("utf-8")
            parsed = json.loads(decoded)
            if not isinstance(parsed, dict):
                raise ValueError("cookies JSON must be an object")
        except Exception as error:
            logger.warning(
                "fragment_cookies_validation_failed error_type=%s",
                type(error).__name__,
            )
            return cookies_base64

        return cookies_base64

    async def check_health(self) -> dict[str, Any]:
        started = time.monotonic()
        try:
            rates = await self.get_rates()
            return {
                "ok": True,
                "rates": rates,
                "response_time": round(time.monotonic() - started, 2),
            }
        except Exception as error:
            return {
                "ok": False,
                "error": str(error),
                "response_time": round(time.monotonic() - started, 2),
            }

    async def get_rates(self) -> dict[str, float]:
        if not self.client:
            raise FragmentAPIError("Fragment API client is not initialized")

        response = await asyncio.to_thread(self.client.get_rates)
        no_kyc_percent = float(_value(response, "rate_no_kyc", 5.0))
        kyc_percent = float(_value(response, "rate_with_kyc", 3.0))
        no_kyc_decimal = float(_value(response, "rate_no_kyc_decimal", no_kyc_percent / 100))
        kyc_decimal = float(_value(response, "rate_with_kyc_decimal", kyc_percent / 100))

        return {
            "no_kyc_percent": no_kyc_percent,
            "kyc_percent": kyc_percent,
            "no_kyc_decimal": no_kyc_decimal,
            "kyc_decimal": kyc_decimal,
        }

    async def estimate_stars_price_usd(self, stars_count: int) -> float:
        rates = await self.get_rates()
        base_usd_per_star = float(os.getenv("FRAGMENT_STAR_BASE_USD", str(settings.fragment_star_base_usd)))
        mode_decimal = rates["kyc_decimal"] if self.api_mode == "kyc" else rates["no_kyc_decimal"]
        return round(stars_count * base_usd_per_star * (1 + mode_decimal), 2)

    async def buy_stars(self, recipient_username: str, stars_count: int) -> str:
        if not self.client:
            raise FragmentAPIError("Fragment API client is not initialized")

        username = recipient_username.strip()
        if not username:
            raise FragmentAPIError("recipient_username is empty")
        if not username.startswith("@"):
            username = f"@{username}"

        logger.info(
            "fragment_buy_stars_started username=%s amount=%s mode=%s",
            username,
            stars_count,
            self.api_mode,
        )

        try:
            result = await asyncio.to_thread(
                self.client.buy_stars,
                username=username,
                amount=stars_count,
                seed=self.wallet_mnemonic_base64,
                cookies=self.cookies_base64,
                wait=True,
            )
        except LibraryFragmentAPIError as error:
            raise FragmentAPIError(str(error)) from error
        except Exception as error:
            raise FragmentAPIError(f"Fragment API error: {error}") from error

        success = _value(result, "success")
        if success is False:
            raise FragmentAPIError(_value(result, "error", "Fragment API returned success=false"))

        transaction_id = (
            _value(result, "transaction_hash")
            or _value(result, "transaction_id")
            or _value(result, "request_id")
            or _value(result, "id")
        )
        if not transaction_id and isinstance(result, str):
            transaction_id = result
        if not transaction_id:
            raise FragmentAPIError(f"Unable to find transaction id in response: {result}")

        logger.info("fragment_purchase_completed transaction_id=%s", transaction_id)
        return str(transaction_id)



class FragmentClient:
    """Compatibility adapter used by the existing FragmentService."""

    def __init__(self, api_service: FragmentAPIService | None = None) -> None:
        self.api_service = api_service or FragmentAPIService(
            wallet_mnemonic=settings.fragment_wallet_mnemonic,
            api_url=settings.fragment_effective_api_url,
            api_mode=settings.fragment_api_mode,
            cookies_base64=settings.fragment_cookies_base64,
        )

    async def buy_stars(
        self,
        *,
        order_id: str,
        recipient: str,
        recipient_tg_id: int,
        amount: int,
    ) -> FragmentDeliveryResult:
        transaction_id = await self.api_service.buy_stars(
            recipient_username=recipient,
            stars_count=amount,
        )
        return FragmentDeliveryResult(
            status=FragmentDeliveryStatus.COMPLETED.value,
            transaction_id=transaction_id,
            is_success=True,
            raw={
                "order_id": order_id,
                "recipient_tg_id": recipient_tg_id,
                "sdk": "bbbuilt/fragment-stars-api",
            },
        )

    async def check_fragment_result(self, transaction_id: str) -> FragmentDeliveryResult:
        return FragmentDeliveryResult(
            status=FragmentDeliveryStatus.COMPLETED.value,
            transaction_id=transaction_id,
            is_success=True,
            raw={"sdk": "bbbuilt/fragment-stars-api", "check_supported": False},
        )


FragmentService = FragmentAPIService

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.services.fragment.base import FragmentDeliveryResult, FragmentDeliveryStatus
from config import settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GiftDeliveryPayload:
    user_id: int
    gift_id: str
    pay_for_upgrade: bool = False
    text: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class GiftDeliveryService:
    async def send_gift(
        self,
        *,
        order_id: str,
        recipient_tg_id: int,
        gift_id: str,
    ) -> FragmentDeliveryResult:
        if recipient_tg_id <= 0:
            return FragmentDeliveryResult(
                status=FragmentDeliveryStatus.FAILED.value,
                is_success=False,
                is_retryable=False,
                raw={"reason": "recipient_tg_id_missing"},
            )

        payload = GiftDeliveryPayload(
            user_id=recipient_tg_id,
            gift_id=gift_id,
            pay_for_upgrade=False,
        )

        url = f"{settings.telegram_api_base_url.rstrip('/')}/bot{settings.bot_token}/sendGift"
        body = {
            "user_id": payload.user_id,
            "gift_id": payload.gift_id,
            "pay_for_upgrade": payload.pay_for_upgrade,
        }
        if payload.text:
            body["text"] = payload.text

        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
                response = await client.post(url, json=body)
                response.raise_for_status()
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as error:
            logger.warning(
                "telegram_gift_delivery_failed order_id=%s gift_id=%s error_type=%s",
                order_id,
                gift_id,
                type(error).__name__,
            )
            return FragmentDeliveryResult(
                status=FragmentDeliveryStatus.FAILED.value,
                is_success=False,
                is_retryable=True,
                raw={"error": type(error).__name__},
            )

        try:
            data = response.json()
        except ValueError:
            logger.warning(
                "telegram_gift_delivery_invalid_json order_id=%s gift_id=%s",
                order_id,
                gift_id,
            )
            return FragmentDeliveryResult(
                status=FragmentDeliveryStatus.FAILED.value,
                is_success=False,
                is_retryable=True,
                raw={"error": "invalid_json"},
            )

        if not data.get("ok", False):
            logger.warning(
                "telegram_gift_delivery_api_not_ok order_id=%s gift_id=%s",
                order_id,
                gift_id,
            )
            return FragmentDeliveryResult(
                status=FragmentDeliveryStatus.FAILED.value,
                is_success=False,
                is_retryable=True,
                raw={"error": "api_not_ok", "response": data},
            )

        tx_id = f"tg_gift_{order_id}_{int(time.time())}"
        logger.info(
            "telegram_gift_delivery_completed order_id=%s gift_id=%s transaction_id=%s",
            order_id,
            gift_id,
            tx_id,
        )
        return FragmentDeliveryResult(
            status=FragmentDeliveryStatus.COMPLETED.value,
            transaction_id=tx_id,
            is_success=True,
            raw={"provider": "telegram_bot_api", "result": data.get("result")},
        )

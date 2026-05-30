import logging

from app.db.models.order import Order
from app.services.fragment.base import (
    FragmentDeliveryResult,
    FragmentDeliveryStatus,
    FragmentError,
)
from app.services.fragment.client import FragmentClient
from config import settings


logger = logging.getLogger(__name__)


class FragmentService:
    def __init__(self, client: FragmentClient | None = None) -> None:
        self.client = client or FragmentClient()
        self.max_delivery_attempts = settings.fragment_max_delivery_attempts

    async def buy_stars(self, order: Order) -> FragmentDeliveryResult:
        if order.status != "paid":
            logger.warning(
                "fragment_delivery_rejected_not_paid order_id=%s status=%s",
                order.id,
                order.status,
            )
            return FragmentDeliveryResult(
                status=FragmentDeliveryStatus.FAILED.value,
                is_success=False,
                is_retryable=False,
                raw={"reason": "order_not_paid"},
            )

        if order.fragment_transaction_id and order.delivery_status == FragmentDeliveryStatus.COMPLETED.value:
            return FragmentDeliveryResult(
                status=FragmentDeliveryStatus.COMPLETED.value,
                transaction_id=order.fragment_transaction_id,
                is_success=True,
                raw={"idempotent": True},
            )

        if order.delivery_attempts >= self.max_delivery_attempts:
            return FragmentDeliveryResult(
                status=FragmentDeliveryStatus.FAILED.value,
                is_success=False,
                is_retryable=False,
                raw={"reason": "max_attempts_reached"},
            )

        try:
            return await self.client.buy_stars(
                order_id=order.order_id or str(order.id),
                recipient=order.recipient or "",
                recipient_tg_id=int(order.recipient_tg_id or 0),
                amount=int(order.amount or 0),
            )
        except FragmentError as error:
            is_retryable = self._is_retryable_error(error)
            logger.exception(
                "fragment_delivery_failed order_id=%s error_type=%s retryable=%s",
                order.id,
                type(error).__name__,
                is_retryable,
            )
            return FragmentDeliveryResult(
                status=(
                    FragmentDeliveryStatus.PENDING.value
                    if is_retryable
                    else FragmentDeliveryStatus.FAILED.value
                ),
                is_success=False,
                is_retryable=is_retryable,
                raw={
                    "error": type(error).__name__,
                    "error_message": str(error),
                },
            )

    async def check_fragment_result(self, transaction_id: str) -> FragmentDeliveryResult:
        return await self.client.check_fragment_result(transaction_id)

    @staticmethod
    def _is_retryable_error(error: FragmentError) -> bool:
        message = str(error).lower()
        non_retryable_markers = (
            "recipient_username is empty",
            "fragment_wallet_mnemonic is empty",
            "buy button is disabled",
            "insufficient balance",
            "not enough balance",
            "recipient not found",
            "user not found",
            "username is invalid",
        )
        if any(marker in message for marker in non_retryable_markers):
            return False

        return True

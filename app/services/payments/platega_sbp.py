import logging
from decimal import Decimal
from typing import Any

import httpx

from app.services.payments.base import (
    PaymentCancelResult,
    PaymentCheckResult,
    PaymentInvoice,
    PaymentProviderError,
    PaymentStatus,
)
from config import settings


logger = logging.getLogger(__name__)


class PlategaSbpPaymentProvider:
    provider_name = "platega_sbp"
    payment_method = 2

    def __init__(
        self,
        base_url: str | None = None,
        merchant_id: str | None = None,
        secret: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.platega_api_base_url).rstrip("/")
        self.merchant_id = merchant_id or settings.platega_merchant_id
        self.secret = secret or settings.platega_secret
        self.timeout_seconds = timeout_seconds or settings.platega_timeout_seconds

    def _headers(self) -> dict[str, str]:
        if not self.merchant_id or not self.secret:
            raise PaymentProviderError("Platega credentials are not configured")

        return {
            "X-MerchantId": self.merchant_id,
            "X-Secret": self.secret,
            "Content-Type": "application/json",
        }

    async def create_invoice(
        self,
        *,
        amount_rub: Decimal,
        order_id: str,
        recipient_tg_id: int,
        payload: str | None = None,
    ) -> PaymentInvoice:
        description = f"TgId:{int(recipient_tg_id)}"
        request_payload: dict[str, Any] = {
            "paymentMethod": self.payment_method,
            "paymentDetails": {
                "amount": float(amount_rub),
                "currency": "RUB",
            },
            "description": description,
            "return": settings.platega_success_url,
            "failedUrl": settings.platega_failed_url,
            "payload": payload or order_id,
        }

        logger.info(
            "platega_create_invoice_started provider=%s order_id=%s recipient_tg_id=%s amount=%s",
            self.provider_name,
            order_id,
            recipient_tg_id,
            amount_rub,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/transaction/process",
                    headers=self._headers(),
                    json=request_payload,
                )
                response.raise_for_status()
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as error:
            logger.exception(
                "platega_create_invoice_failed provider=%s order_id=%s error_type=%s",
                self.provider_name,
                order_id,
                type(error).__name__,
            )
            raise PaymentProviderError("Unable to create Platega invoice") from error

        data = response.json()
        transaction_id = str(data.get("transactionId") or data.get("id") or "")
        payment_url = str(
            data.get("payment_url")
            or data.get("paymentUrl")
            or data.get("payUrl")
            or data.get("redirect")
            or data.get("url")
            or ""
        )

        if not transaction_id or not payment_url:
            logger.error(
                "platega_create_invoice_invalid_response provider=%s order_id=%s response_keys=%s",
                self.provider_name,
                order_id,
                sorted(data.keys()),
            )
            raise PaymentProviderError("Platega invoice response is invalid")

        payable_amount = self._extract_payable_amount(data, amount_rub)

        return PaymentInvoice(
            transaction_id=transaction_id,
            payment_url=payment_url,
            status=self._normalize_status(str(data.get("status", PaymentStatus.PENDING))),
            provider=self.provider_name,
            amount=payable_amount,
            raw=data,
        )

    async def check_payment(self, transaction_id: str) -> PaymentCheckResult:
        logger.info(
            "platega_check_payment_started provider=%s transaction_id=%s",
            self.provider_name,
            transaction_id,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    f"{self.base_url}/transaction/{transaction_id}",
                    headers=self._headers(),
                )
                response.raise_for_status()
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as error:
            logger.exception(
                "platega_check_payment_failed provider=%s transaction_id=%s error_type=%s",
                self.provider_name,
                transaction_id,
                type(error).__name__,
            )
            raise PaymentProviderError("Unable to check Platega payment") from error

        data = response.json()
        status = self._normalize_status(str(data.get("status", PaymentStatus.PENDING)))
        return PaymentCheckResult(
            transaction_id=transaction_id,
            status=status,
            provider=self.provider_name,
            is_paid=status == PaymentStatus.PAID,
            raw=data,
        )

    async def cancel_invoice(self, transaction_id: str) -> PaymentCancelResult:
        logger.info(
            "platega_cancel_invoice_unsupported provider=%s transaction_id=%s",
            self.provider_name,
            transaction_id,
        )
        return PaymentCancelResult(
            transaction_id=transaction_id,
            status=PaymentStatus.CANCELED.value,
            provider=self.provider_name,
            raw={"supported": False},
        )

    @staticmethod
    def _normalize_status(status: str) -> str:
        normalized = status.lower()
        if normalized in {"success", "succeeded", "completed", "paid", "confirmed"}:
            return PaymentStatus.PAID.value
        if normalized in {"chargeback", "refunded", "refund"}:
            return PaymentStatus.REFUNDED.value
        if normalized in {"cancelled", "canceled"}:
            return PaymentStatus.CANCELED.value
        if normalized in {"failed", "error", "declined"}:
            return PaymentStatus.FAILED.value
        return PaymentStatus.PENDING.value

    @staticmethod
    def _extract_payable_amount(data: dict[str, Any], fallback_amount: Decimal) -> Decimal:
        direct_keys = (
            "paymentAmount",
            "payAmount",
            "amountWithFee",
            "amount_with_fee",
            "totalAmount",
            "total_amount",
            "total",
            "payerAmount",
            "customerAmount",
        )
        nested_keys = (
            ("paymentDetails", "amountWithFee"),
            ("paymentDetails", "totalAmount"),
            ("paymentDetails", "payerAmount"),
            ("paymentDetails", "customerAmount"),
            ("payment", "amountWithFee"),
            ("payment", "totalAmount"),
        )

        for key in direct_keys:
            value = data.get(key)
            if value is not None:
                return PlategaSbpPaymentProvider._to_money(value)

        for section_key, amount_key in nested_keys:
            section = data.get(section_key)
            if isinstance(section, dict):
                value = section.get(amount_key)
                if value is not None:
                    return PlategaSbpPaymentProvider._to_money(value)

        multiplier = Decimal("1") + Decimal(str(settings.platega_display_commission_percent)) / Decimal("100")
        return PlategaSbpPaymentProvider._to_money(fallback_amount * multiplier)

    @staticmethod
    def _to_money(value: Any) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.01"))

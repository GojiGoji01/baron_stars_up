from decimal import Decimal, ROUND_UP
from typing import Any

import httpx

from app.services.exchange_rate import get_usdt_rub_rate
from app.services.payments.base import (
    BasePaymentProvider,
    PaymentCancelResult,
    PaymentCheckResult,
    PaymentInvoice,
    PaymentProviderError,
    PaymentStatus,
)
from config import settings


class CryptoPaymentProvider(BasePaymentProvider):
    provider_name = "cryptobot"
    payment_method = "cryptobot"

    def __init__(
        self,
        api_token: str | None = None,
        base_url: str | None = None,
        asset: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.api_token = api_token or settings.cryptobot_api_token
        self.base_url = (base_url or settings.cryptobot_api_base_url).rstrip("/")
        self.asset = (asset or settings.cryptobot_asset).upper()
        self.timeout_seconds = timeout_seconds or settings.http_timeout

    def _headers(self) -> dict[str, str]:
        if not self.api_token:
            raise PaymentProviderError("CryptoBot API token is not configured")

        return {
            "Crypto-Pay-API-Token": self.api_token,
            "Content-Type": "application/json",
        }

    async def create_invoice(self, order) -> PaymentInvoice:
        order_id = str(order.order_id)
        amount_rub = Decimal(str(getattr(order, "price_rub", getattr(order, "price", "0"))))
        amount_crypto = await self._rub_to_crypto_amount(amount_rub)
        payload = {
            "asset": self.asset,
            "amount": str(amount_crypto),
            "description": f"Order {order_id}",
            "payload": order_id,
            "expires_in": settings.cryptobot_invoice_expires_seconds,
        }

        data = await self._request("POST", "/createInvoice", json=payload)
        invoice = data.get("result")
        if not isinstance(invoice, dict):
            raise PaymentProviderError("CryptoBot invoice response is invalid")

        invoice_id = str(invoice.get("invoice_id") or "")
        payment_url = str(invoice.get("pay_url") or invoice.get("bot_invoice_url") or invoice.get("mini_app_invoice_url") or "")
        if not invoice_id or not payment_url:
            raise PaymentProviderError("CryptoBot invoice response has no invoice id or payment url")

        return PaymentInvoice(
            transaction_id=invoice_id,
            order_id=order_id,
            provider=self.provider_name,
            amount=amount_crypto,
            payment_url=payment_url,
            status=self._normalize_status(str(invoice.get("status", PaymentStatus.PENDING))),
            raw=invoice,
        )

    async def check_payment(self, transaction_id: str) -> PaymentCheckResult:
        data = await self._request("GET", "/getInvoices", params={"invoice_ids": transaction_id})
        invoice = self._extract_invoice(data)
        status = self._normalize_status(str(invoice.get("status", PaymentStatus.PENDING)))
        return PaymentCheckResult(
            transaction_id=transaction_id,
            status=status,
            provider=self.provider_name,
            is_paid=status == PaymentStatus.PAID.value,
            raw=invoice,
        )

    async def cancel_invoice(self, transaction_id: str) -> PaymentCancelResult:
        data = await self._request("POST", "/deleteInvoice", json={"invoice_id": int(transaction_id)})
        return PaymentCancelResult(
            transaction_id=transaction_id,
            status=PaymentStatus.CANCELED.value,
            provider=self.provider_name,
            raw=data,
        )

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    headers=self._headers(),
                    **kwargs,
                )
                response.raise_for_status()
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as error:
            raise PaymentProviderError("CryptoBot API request failed") from error

        try:
            data = response.json()
        except ValueError as error:
            raise PaymentProviderError("CryptoBot API response is not JSON") from error

        if not data.get("ok", False):
            raise PaymentProviderError(str(data.get("error") or "CryptoBot API returned not ok"))

        return data

    async def _rub_to_crypto_amount(self, amount_rub: Decimal) -> Decimal:
        rate = Decimal(str(await get_usdt_rub_rate()))
        if rate <= Decimal("0"):
            raise PaymentProviderError("USDT/RUB rate is invalid")

        return (amount_rub / rate).quantize(Decimal("0.01"), rounding=ROUND_UP)

    @staticmethod
    def _extract_invoice(data: dict[str, Any]) -> dict[str, Any]:
        result = data.get("result")
        if isinstance(result, dict):
            items = result.get("items")
            if isinstance(items, list) and items:
                invoice = items[0]
                if isinstance(invoice, dict):
                    return invoice

            if "invoice_id" in result:
                return result

        raise PaymentProviderError("CryptoBot invoice was not found")

    @staticmethod
    def _normalize_status(status: str) -> str:
        normalized = status.lower()
        if normalized == "paid":
            return PaymentStatus.PAID.value
        if normalized in {"deleted", "expired", "canceled", "cancelled"}:
            return PaymentStatus.CANCELED.value
        if normalized in {"failed", "error"}:
            return PaymentStatus.FAILED.value
        return PaymentStatus.PENDING.value

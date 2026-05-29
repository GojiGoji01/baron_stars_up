from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any, Protocol


class PaymentStatus(StrEnum):
    CREATED = "created"
    PENDING = "pending"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    CANCELED = "canceled"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentProviderError(Exception):
    pass


@dataclass(frozen=True)
class PaymentInvoice:
    transaction_id: str
    payment_url: str
    status: str
    provider: str
    amount: Decimal
    order_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def invoice_id(self) -> str:
        return self.transaction_id

    @property
    def pay_url(self) -> str:
        return self.payment_url

    @property
    def payment_method(self) -> str:
        return self.provider


@dataclass(frozen=True)
class PaymentCheckResult:
    transaction_id: str
    status: str
    provider: str
    is_paid: bool
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PaymentCancelResult:
    transaction_id: str
    status: str
    provider: str
    raw: dict[str, Any] = field(default_factory=dict)


class BasePaymentProvider(Protocol):
    provider_name: str

    async def create_invoice(
        self,
        *,
        amount_rub: Decimal,
        order_id: str,
        recipient_tg_id: int,
        payload: str | None = None,
    ) -> PaymentInvoice:
        raise NotImplementedError

    async def check_payment(self, transaction_id: str) -> PaymentCheckResult:
        raise NotImplementedError

    async def cancel_invoice(self, transaction_id: str) -> PaymentCancelResult:
        raise NotImplementedError

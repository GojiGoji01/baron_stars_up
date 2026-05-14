from dataclasses import dataclass
from enum import StrEnum

from app.services.orders import Order


class PaymentStatus(StrEnum):
    CREATED = "created"
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"
    FAILED = "failed"


@dataclass(frozen=True)
class PaymentInvoice:
    invoice_id: str
    order_id: str
    payment_method: str
    amount: int | float
    pay_url: str
    status: str


class BasePaymentProvider:
    payment_method: str

    async def create_invoice(self, order: Order) -> PaymentInvoice:
        raise NotImplementedError

    async def check_payment(self, invoice_id: str) -> PaymentStatus:
        raise NotImplementedError

    async def cancel_invoice(self, invoice_id: str) -> PaymentStatus:
        raise NotImplementedError

import asyncio
from decimal import Decimal
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.checkout import CheckoutError, CheckoutService
from app.services.fragment.base import FragmentDeliveryResult, FragmentDeliveryStatus
from app.services.payments.base import PaymentCheckResult, PaymentInvoice, PaymentStatus


class _Order:
    def __init__(self, oid: int, order_id: str, user_id: int, recipient: str, recipient_tg_id: int, amount: int, price_rub: Decimal):
        self.id = oid
        self.order_id = order_id
        self.user_id = user_id
        self.order_type = "stars"
        self.recipient = recipient
        self.recipient_tg_id = recipient_tg_id
        self.amount = amount
        self.price_rub = price_rub
        self.payment_provider = "platega_sbp"
        self.payment_transaction_id = None
        self.payment_url = None
        self.status = "pending"
        self.delivery_status = None
        self.delivery_attempts = 0
        self.fragment_transaction_id = None
        self.gift_id = None


class _OrdersRepoProxy:
    def __init__(self, service):
        self.service = service

    async def increment_delivery_attempts(self, order_id: int):
        order = self.service.storage[order_id]
        order.delivery_attempts += 1
        return order


class _OrdersService:
    def __init__(self):
        self.storage = {}
        self.next_id = 1
        self.orders = _OrdersRepoProxy(self)

    async def create_stars_order(self, *, user_id, recipient, recipient_tg_id, amount, price_rub, status):
        order = _Order(self.next_id, f"ORD{self.next_id:08d}", user_id, recipient, recipient_tg_id, amount, price_rub)
        order.status = status
        self.storage[order.id] = order
        self.next_id += 1
        return order

    async def get_order_by_id(self, order_id: int):
        return self.storage.get(order_id)

    async def update_status(self, order_id: int, status: str):
        order = self.storage[order_id]
        order.status = status
        return order

    async def update_order(self, order_id: int, **fields):
        order = self.storage[order_id]
        for key, value in fields.items():
            setattr(order, key, value)
        return order


class _PaymentProvider:
    provider_name = "platega_sbp"

    def __init__(self):
        self.is_paid = False
        self.status = PaymentStatus.PENDING.value

    async def create_invoice(self, *, amount_rub, order_id, recipient_tg_id, payload=None):
        return PaymentInvoice(
            transaction_id=f"tx_{order_id}",
            payment_url=f"https://pay.local/{order_id}",
            status=PaymentStatus.PENDING.value,
            provider=self.provider_name,
            amount=Decimal(str(amount_rub)),
        )

    async def check_payment(self, transaction_id: str):
        return PaymentCheckResult(
            transaction_id=transaction_id,
            status=self.status,
            provider=self.provider_name,
            is_paid=self.is_paid,
            raw={},
        )


class _FragmentService:
    def __init__(self):
        self.calls = 0
        self.result = FragmentDeliveryResult(
            status=FragmentDeliveryStatus.COMPLETED.value,
            transaction_id="frag_tx_ok",
            is_success=True,
            raw={},
        )

    async def buy_stars(self, order):
        self.calls += 1
        return self.result


class _Antifraud:
    class Result:
        is_allowed = True

    async def check_recipient(self, **kwargs):
        return self.Result()


class _DeliveryAttempts:
    def __init__(self):
        self.last_id = 0
        self.status_by_order = {}

    async def start_attempt(self, *, order_id, attempt_key, provider):
        self.last_id += 1
        return type("Attempt", (), {"id": self.last_id})

    async def mark_completed(self, *, attempt_id, external_transaction_id):
        return None

    async def mark_failed(self, *, attempt_id, error_message):
        return None

    async def mark_verification_required(self, *, attempt_id, error_message, external_transaction_id=None):
        return None

    async def get_latest_for_order(self, *, order_id):
        status = self.status_by_order.get(order_id)
        if not status:
            return None
        return type("Attempt", (), {"status": status})


class _Referrals:
    async def accrue_after_completed(self, order):
        return None


async def run() -> None:
    payment = _PaymentProvider()
    fragment = _FragmentService()
    service = CheckoutService(
        session=None,
        payment_provider=payment,
        fragment_service=fragment,
        antifraud_service=_Antifraud(),
    )
    service.orders_service = _OrdersService()
    service.delivery_attempts_service = _DeliveryAttempts()
    service.referrals_service = _Referrals()

    checkout = await service.create_stars_checkout(
        user_id=1001,
        recipient="@smoke_user",
        recipient_tg_id=1001,
        amount=50,
    )
    assert checkout.order.status == "pending_payment"
    assert checkout.order.payment_transaction_id is not None

    payment.is_paid = True
    payment.status = PaymentStatus.PAID.value
    result = await service.confirm_payment_and_deliver(order_id=checkout.order.id)
    assert result.order.status == "completed"
    assert result.delivery_status == FragmentDeliveryStatus.COMPLETED.value
    assert fragment.calls == 1

    retry = await service.retry_delivery(order_id=checkout.order.id)
    assert retry.order.status == "completed"
    assert fragment.calls == 1

    print("E2E smoke passed: create -> paid -> delivery -> idempotent retry")


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except CheckoutError as error:
        raise SystemExit(f"E2E smoke failed: {error}") from error

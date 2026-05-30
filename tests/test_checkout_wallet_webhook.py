import asyncio
from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.services.checkout import CheckoutService, CheckoutError
from app.services.fragment.base import FragmentDeliveryResult, FragmentDeliveryStatus
from app.services.payments.base import PaymentCheckResult, PaymentInvoice, PaymentStatus
from app.services.wallet import WalletBindingError, WalletService
from app.webhooks import _recheck_and_apply_non_paid_status


@dataclass
class FakeOrder:
    id: int
    order_id: str
    user_id: int
    order_type: str
    recipient: str
    recipient_tg_id: int
    amount: int
    price_rub: Decimal
    payment_provider: str
    payment_transaction_id: str | None = None
    payment_url: str | None = None
    status: str = "created"
    delivery_status: str | None = None
    delivery_attempts: int = 0
    fragment_transaction_id: str | None = None
    gift_id: str | None = None


class FakeOrdersRepoProxy:
    def __init__(self, service):
        self.service = service

    async def increment_delivery_attempts(self, order_id: int):
        order = self.service.storage[order_id]
        order.delivery_attempts += 1
        return order


class FakeOrdersService:
    def __init__(self):
        self.storage: dict[int, FakeOrder] = {}
        self.next_id = 1
        self.orders = FakeOrdersRepoProxy(self)

    async def create_stars_order(self, *, user_id, recipient, recipient_tg_id, amount, price_rub, status):
        order = FakeOrder(
            id=self.next_id,
            order_id=f"ORD{self.next_id:08d}",
            user_id=user_id,
            order_type="stars",
            recipient=recipient,
            recipient_tg_id=recipient_tg_id,
            amount=amount,
            price_rub=price_rub,
            payment_provider="platega_sbp",
            status=status,
        )
        self.storage[order.id] = order
        self.next_id += 1
        return order

    async def get_order_by_id(self, order_id: int):
        return self.storage.get(order_id)

    async def get_order_by_id_for_update(self, order_id: int):
        return await self.get_order_by_id(order_id)

    async def update_status(self, order_id: int, status: str):
        order = self.storage[order_id]
        order.status = status
        return order

    async def update_order(self, order_id: int, **fields):
        order = self.storage[order_id]
        for k, v in fields.items():
            setattr(order, k, v)
        return order


class FakePaymentProvider:
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


class FakeFragmentService:
    def __init__(self):
        self.calls = 0
        self.next_result = FragmentDeliveryResult(
            status=FragmentDeliveryStatus.COMPLETED.value,
            transaction_id="frag_tx_1",
            is_success=True,
            raw={},
        )

    async def buy_stars(self, order):
        self.calls += 1
        return self.next_result


class FakeAntifraudService:
    class Result:
        is_allowed = True

    async def check_recipient(self, **kwargs):
        return self.Result()


class FakeReferralService:
    async def accrue_after_completed(self, order):
        return None


@dataclass
class FakeAttempt:
    id: int
    order_id: int
    status: str


class FakeDeliveryAttemptsService:
    def __init__(self):
        self.items: list[FakeAttempt] = []
        self.last_id = 0

    async def start_attempt(self, *, order_id, attempt_key, provider):
        self.last_id += 1
        item = FakeAttempt(id=self.last_id, order_id=order_id, status="started")
        self.items.append(item)
        return item

    async def start_attempt_or_get(self, *, order_id, attempt_key, provider):
        for item in self.items:
            if getattr(item, "attempt_key", None) == attempt_key:
                return item, False
        self.last_id += 1
        item = FakeAttempt(id=self.last_id, order_id=order_id, status="started")
        setattr(item, "attempt_key", attempt_key)
        self.items.append(item)
        return item, True

    async def mark_completed(self, *, attempt_id, external_transaction_id):
        for item in self.items:
            if item.id == attempt_id:
                item.status = "completed"
                return item
        return None

    async def mark_failed(self, *, attempt_id, error_message):
        for item in self.items:
            if item.id == attempt_id:
                item.status = "failed"
                return item
        return None

    async def mark_verification_required(self, *, attempt_id, error_message, external_transaction_id=None):
        for item in self.items:
            if item.id == attempt_id:
                item.status = "verification_required"
                return item
        return None

    async def get_latest_for_order(self, *, order_id):
        for item in reversed(self.items):
            if item.order_id == order_id:
                return item
        return None


def _build_checkout_service():
    payment = FakePaymentProvider()
    fragment = FakeFragmentService()
    service = CheckoutService(
        session=None,  # replaced by fakes below
        payment_provider=payment,
        fragment_service=fragment,
        antifraud_service=FakeAntifraudService(),
    )
    service.orders_service = FakeOrdersService()
    service.referrals_service = FakeReferralService()
    service.delivery_attempts_service = FakeDeliveryAttemptsService()
    return service, payment, fragment


def test_order_create_and_confirm_paid_and_delivery():
    async def run():
        service, payment, fragment = _build_checkout_service()
        checkout = await service.create_stars_checkout(
            user_id=1,
            recipient="@alice",
            recipient_tg_id=123,
            amount=50,
        )
        assert checkout.order.status == "pending_payment"
        assert checkout.order.payment_transaction_id is not None

        payment.is_paid = False
        payment.status = PaymentStatus.PENDING.value
        pending = await service.confirm_payment_and_deliver(order_id=checkout.order.id)
        assert pending.payment_status == PaymentStatus.PENDING.value
        assert fragment.calls == 0

        payment.is_paid = True
        payment.status = PaymentStatus.PAID.value
        paid = await service.confirm_payment_and_deliver(order_id=checkout.order.id)
        assert paid.delivery_status == FragmentDeliveryStatus.COMPLETED.value
        assert paid.order.status == "completed"
        assert fragment.calls == 1

    asyncio.run(run())


def test_retry_blocked_on_verification_required_for_stars():
    async def run():
        service, payment, fragment = _build_checkout_service()
        checkout = await service.create_stars_checkout(
            user_id=2,
            recipient="@bob",
            recipient_tg_id=222,
            amount=100,
        )
        payment.is_paid = True
        payment.status = PaymentStatus.PAID.value
        fragment.next_result = FragmentDeliveryResult(
            status=FragmentDeliveryStatus.PENDING.value,
            transaction_id=None,
            is_success=False,
            is_retryable=True,
            raw={"error_message": "timeout"},
        )
        first = await service.confirm_payment_and_deliver(order_id=checkout.order.id)
        assert first.order.status == "delivery_failed"
        assert first.user_message is not None

        with pytest.raises(CheckoutError):
            await service.retry_delivery(order_id=checkout.order.id)

    asyncio.run(run())


def test_webhook_non_paid_recheck_updates_status_and_not_blind(monkeypatch):
    async def run():
        class FakeOrdersServiceForWebhook:
            def __init__(self):
                self.updated: list[str] = []

            async def update_status(self, order_id: int, status: str):
                self.updated.append(status)

        class FakeProvider:
            async def check_payment(self, transaction_id: str):
                return PaymentCheckResult(
                    transaction_id=transaction_id,
                    status=PaymentStatus.CANCELED.value,
                    provider="platega_sbp",
                    is_paid=False,
                    raw={},
                )

        order = FakeOrder(
            id=77,
            order_id="ORD00000077",
            user_id=7,
            order_type="stars",
            recipient="@z",
            recipient_tg_id=7,
            amount=10,
            price_rub=Decimal("10.00"),
            payment_provider="platega_sbp",
            payment_transaction_id="tx_77",
            status="pending_payment",
        )
        orders = FakeOrdersServiceForWebhook()

        monkeypatch.setattr("app.webhooks._get_payment_provider", lambda provider_name: FakeProvider())
        called = {"confirm": 0}

        async def fake_confirm(session, *, order_id: int):
            called["confirm"] += 1

        monkeypatch.setattr("app.webhooks.confirm_payment_and_deliver", fake_confirm)

        await _recheck_and_apply_non_paid_status(
            session=object(),
            orders_service=orders,
            order=order,
            webhook_status="canceled",
        )
        assert called["confirm"] == 0
        assert orders.updated == ["canceled"]

    asyncio.run(run())


def test_wallet_binding_conflict_between_users():
    class InMemoryUsersRepository:
        def __init__(self):
            self.wallet_owner: dict[str, int] = {}
            self.users = {
                1: {"telegram_id": 1, "wallet_address": None, "wallet_provider": None, "wallet_status": None},
                2: {"telegram_id": 2, "wallet_address": None, "wallet_provider": None, "wallet_status": None},
            }

        async def bind_wallet(self, *, telegram_id, wallet_address, wallet_provider):
            owner = self.wallet_owner.get(wallet_address)
            if owner is not None and owner != telegram_id:
                raise ValueError("wallet address is already bound to another user")
            self.wallet_owner[wallet_address] = telegram_id
            user = self.users[telegram_id]
            user["wallet_address"] = wallet_address
            user["wallet_provider"] = wallet_provider
            user["wallet_status"] = "connected"
            return type("U", (), user)

        async def disconnect_wallet(self, *, telegram_id):
            user = self.users.get(telegram_id)
            if user is None:
                return None
            if user["wallet_address"]:
                self.wallet_owner.pop(user["wallet_address"], None)
            user["wallet_address"] = None
            user["wallet_provider"] = None
            user["wallet_status"] = "disconnected"
            return type("U", (), user)

        async def touch_wallet_verified_at(self, *, telegram_id):
            user = self.users.get(telegram_id)
            if user is None:
                return None
            return type("U", (), user)

    async def run():
        service = WalletService(session=None)
        service.users = InMemoryUsersRepository()

        first = await service.connect_wallet(telegram_id=1, wallet_address="EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        assert first.wallet_status == "connected"
        with pytest.raises(WalletBindingError):
            await service.connect_wallet(telegram_id=2, wallet_address="EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")

    asyncio.run(run())

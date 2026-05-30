import asyncio
from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.services.admin import AdminService


@dataclass
class _Order:
    id: int
    status: str
    delivery_status: str | None = None
    amount_rub: Decimal = Decimal("0.00")


class _FakeOrdersRepository:
    def __init__(self, order: _Order | None) -> None:
        self.order = order
        self.updated: dict[str, str] | None = None

    async def get_order_by_id(self, order_id: int):
        if self.order and self.order.id == order_id:
            return self.order
        return None

    async def update_order(self, order_id: int, **fields):
        if self.order is None or self.order.id != order_id:
            return None
        for key, value in fields.items():
            setattr(self.order, key, value)
        self.updated = {key: str(value) for key, value in fields.items()}
        return self.order


def _build_service(order: _Order | None) -> AdminService:
    service = AdminService(session_or_orders_service=object())
    service.orders = _FakeOrdersRepository(order)
    return service


def test_refund_allowed_for_paid_like_statuses():
    async def run():
        for status in ("paid", "delivery_pending", "delivery_failed", "completed"):
            order = _Order(id=1, status=status)
            service = _build_service(order)
            updated = await service.refund_request(order_id=1)
            assert updated is not None
            assert updated.status == "refunded"
            assert updated.delivery_status == "failed"

    asyncio.run(run())


def test_refund_rejected_for_non_paid_statuses():
    async def run():
        order = _Order(id=2, status="pending_payment")
        service = _build_service(order)
        with pytest.raises(ValueError):
            await service.refund_request(order_id=2)

    asyncio.run(run())


def test_refund_no_order_returns_none():
    async def run():
        service = _build_service(order=None)
        updated = await service.refund_request(order_id=999)
        assert updated is None

    asyncio.run(run())

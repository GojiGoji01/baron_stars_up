from collections.abc import Sequence
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order


class OrderStatus(StrEnum):
    CREATED = "created"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class OrdersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_order(
        self,
        user_id: int,
        amount_rub: Decimal,
        cost_price: Decimal,
        status: str = OrderStatus.CREATED,
        profit_amount: Decimal = Decimal("0.00"),
        referral_profit: Decimal = Decimal("0.00"),
    ) -> Order:
        order = Order(
            user_id=user_id,
            amount_rub=amount_rub,
            cost_price=cost_price,
            profit_amount=profit_amount,
            referral_profit=referral_profit,
            status=status,
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def get_order_by_id(self, order_id: int) -> Order | None:
        return await self.session.get(Order, order_id)

    async def update_order(self, order_id: int, **fields: Any) -> Order | None:
        order = await self.get_order_by_id(order_id)
        if order is None:
            return None

        for field, value in fields.items():
            if hasattr(order, field):
                setattr(order, field, value)

        await self.session.flush()
        return order

    async def update_status(self, order_id: int, status: str) -> Order | None:
        return await self.update_order(order_id, status=status)

    async def set_pending_payment(self, order_id: int) -> Order | None:
        return await self.update_status(order_id, OrderStatus.PENDING_PAYMENT)

    async def mark_paid(self, order_id: int) -> Order | None:
        return await self.update_status(order_id, OrderStatus.PAID)

    async def mark_completed(self, order_id: int) -> Order | None:
        return await self.update_status(order_id, OrderStatus.COMPLETED)

    async def mark_failed(self, order_id: int) -> Order | None:
        return await self.update_status(order_id, OrderStatus.FAILED)

    async def mark_refunded(self, order_id: int) -> Order | None:
        return await self.update_status(order_id, OrderStatus.REFUNDED)

    async def list_orders(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
    ) -> Sequence[Order]:
        query = select(Order).order_by(Order.id.desc()).limit(limit).offset(offset)
        if status is not None:
            query = query.where(Order.status == status)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_orders_by_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Order]:
        result = await self.session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def add(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        return order


OrderRepository = OrdersRepository

from collections.abc import Sequence
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order


class OrderStatus(StrEnum):
    CREATED = "created"
    PENDING = "pending"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    CANCELED = "canceled"
    DELIVERY_PENDING = "delivery_pending"
    COMPLETED = "completed"
    DELIVERY_FAILED = "delivery_failed"
    FAILED = "failed"
    REFUNDED = "refunded"


class DeliveryStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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
        order_id: str | None = None,
        order_type: str | None = None,
        recipient: str | None = None,
        recipient_tg_id: int | None = None,
        gift_id: str | None = None,
        amount: int | None = None,
        price_rub: Decimal | None = None,
        payment_provider: str | None = None,
        payment_transaction_id: str | None = None,
        payment_url: str | None = None,
        delivery_status: str | None = None,
        delivery_attempts: int = 0,
        fragment_transaction_id: str | None = None,
    ) -> Order:
        order = Order(
            order_id=order_id,
            user_id=user_id,
            order_type=order_type,
            recipient=recipient,
            recipient_tg_id=recipient_tg_id,
            gift_id=gift_id,
            amount=amount,
            amount_rub=amount_rub,
            price_rub=price_rub or amount_rub,
            cost_price=cost_price,
            profit_amount=profit_amount,
            referral_profit=referral_profit,
            payment_provider=payment_provider,
            payment_transaction_id=payment_transaction_id,
            payment_url=payment_url,
            status=status,
            delivery_status=delivery_status,
            delivery_attempts=delivery_attempts,
            fragment_transaction_id=fragment_transaction_id,
        )
        self.session.add(order)
        await self.session.flush()

        if not order.order_id:
            order.order_id = f"ORD{int(order.id):08d}"
            await self.session.flush()

        return order

    async def get_order_by_id(self, order_id: int) -> Order | None:
        return await self.session.get(Order, order_id)

    async def get_order_by_id_for_update(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.id == order_id).with_for_update()
        )
        return result.scalar_one_or_none()

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

    async def get_order_by_payment_transaction_id(self, transaction_id: str) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.payment_transaction_id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def get_order_by_order_id(self, order_id: str) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.order_id == order_id)
        )
        return result.scalar_one_or_none()

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

    async def increment_delivery_attempts(self, order_id: int) -> Order | None:
        updated_row = await self.session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(delivery_attempts=Order.delivery_attempts + 1)
            .returning(Order.id)
        )
        row = updated_row.first()
        if row is None:
            return None

        await self.session.flush()
        return await self.get_order_by_id(order_id)

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

    async def get_referral_earnings_by_user_ids(self, user_ids: Sequence[int]) -> dict[int, Decimal]:
        if not user_ids:
            return {}

        result = await self.session.execute(
            select(
                Order.user_id,
                func.coalesce(func.sum(Order.referral_profit), 0),
            )
            .where(Order.user_id.in_(tuple(user_ids)))
            .where(Order.status == OrderStatus.COMPLETED)
            .group_by(Order.user_id)
        )
        return {
            int(user_id): Decimal(str(total))
            for user_id, total in result.all()
        }

    async def get_completed_order_counts_by_user_ids(self, user_ids: Sequence[int]) -> dict[int, int]:
        if not user_ids:
            return {}

        result = await self.session.execute(
            select(
                Order.user_id,
                func.count(Order.id),
            )
            .where(Order.user_id.in_(tuple(user_ids)))
            .where(Order.status == OrderStatus.COMPLETED)
            .group_by(Order.user_id)
        )
        return {
            int(user_id): int(total)
            for user_id, total in result.all()
        }

    async def add(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        return order


OrderRepository = OrdersRepository

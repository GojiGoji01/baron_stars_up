from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order as DbOrder
from app.repositories.orders import OrderStatus as DbOrderStatus
from app.repositories.orders import OrdersRepository


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


class OrdersService:
    def __init__(self, session: AsyncSession) -> None:
        self.orders = OrdersRepository(session)

    async def create_order(
        self,
        user_id: int,
        amount_rub: Decimal,
        cost_price: Decimal,
        status: str = DbOrderStatus.CREATED,
        referral_profit: Decimal = Decimal("0.00"),
        order_type: str | None = None,
        recipient: str | None = None,
        recipient_tg_id: int | None = None,
        gift_id: str | None = None,
        amount: int | None = None,
        price_rub: Decimal | None = None,
        payment_provider: str | None = None,
        delivery_status: str | None = None,
    ) -> DbOrder:
        profit_amount = amount_rub - cost_price
        return await self.orders.create_order(
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
            status=status,
            delivery_status=delivery_status,
        )

    async def create_stars_order(
        self,
        user_id: int,
        recipient: str,
        recipient_tg_id: int,
        amount: int,
        price_rub: Decimal,
        status: str = DbOrderStatus.PENDING,
    ) -> DbOrder:
        return await self.create_order(
            user_id=user_id,
            amount_rub=price_rub,
            cost_price=Decimal("0.00"),
            status=status,
            order_type="stars",
            recipient=recipient,
            recipient_tg_id=recipient_tg_id,
            amount=amount,
            price_rub=price_rub,
            payment_provider="platega_sbp",
            delivery_status=None,
        )

    async def create_gift_order(
        self,
        user_id: int,
        recipient: str,
        recipient_tg_id: int,
        gift_id: str,
        price_rub: Decimal,
        status: str = DbOrderStatus.PENDING,
    ) -> DbOrder:
        return await self.create_order(
            user_id=user_id,
            amount_rub=price_rub,
            cost_price=Decimal("0.00"),
            status=status,
            order_type="gift",
            recipient=recipient,
            recipient_tg_id=recipient_tg_id,
            gift_id=gift_id,
            amount=1,
            price_rub=price_rub,
            payment_provider="platega_sbp",
            delivery_status=None,
        )

    async def update_status(self, order_id: int, status: str) -> DbOrder | None:
        return await self.orders.update_status(order_id=order_id, status=status)

    async def update_order(self, order_id: int, **fields: Any) -> DbOrder | None:
        return await self.orders.update_order(order_id, **fields)

    async def get_order_by_id(self, order_id: int) -> DbOrder | None:
        return await self.orders.get_order_by_id(order_id)

    async def get_order_by_order_id(self, order_id: str) -> DbOrder | None:
        return await self.orders.get_order_by_order_id(order_id)

    async def get_order_by_payment_transaction_id(self, transaction_id: str) -> DbOrder | None:
        return await self.orders.get_order_by_payment_transaction_id(transaction_id)

    async def get_all_orders(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
    ) -> list[DbOrder]:
        orders = await self.orders.list_orders(
            limit=limit,
            offset=offset,
            status=status,
        )
        return list(orders)

    async def get_by_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DbOrder]:
        orders = await self.orders.list_orders_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        return list(orders)

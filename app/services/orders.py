from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import StrEnum
from itertools import count
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order as DbOrder
from app.repositories.orders import OrderStatus as DbOrderStatus
from app.repositories.orders import OrdersRepository


class OrderStatus(StrEnum):
    CREATED = "created"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    CANCELED = "canceled"
    FAILED = "failed"


@dataclass
class Order:
    order_id: str
    user_id: int
    order_type: str
    recipient: str
    amount: int | float
    price: int | float
    payment_method: str
    status: str


_ORDER_COUNTER = count(1)
_ORDERS: dict[str, Order] = {}


def _generate_order_id() -> str:
    return f"ORD{next(_ORDER_COUNTER):06d}"


async def create_order(
    user_id: int,
    order_type: str,
    recipient: str,
    amount: int | float,
    price: int | float,
    payment_method: str,
    status: OrderStatus = OrderStatus.CREATED,
) -> Order:
    order = Order(
        order_id=_generate_order_id(),
        user_id=user_id,
        order_type=order_type,
        recipient=recipient,
        amount=amount,
        price=price,
        payment_method=payment_method,
        status=status.value,
    )
    _ORDERS[order.order_id] = order

    return order


async def get_order(order_id: str) -> Order | None:
    return _ORDERS.get(order_id)


async def update_order_status(order_id: str, status: OrderStatus) -> Order | None:
    order = await get_order(order_id)
    if order is None:
        return None

    order.status = status.value
    return order


async def serialize_order(order: Order) -> dict[str, Any]:
    return asdict(order)


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
    ) -> DbOrder:
        profit_amount = amount_rub - cost_price
        return await self.orders.create_order(
            user_id=user_id,
            amount_rub=amount_rub,
            cost_price=cost_price,
            profit_amount=profit_amount,
            referral_profit=referral_profit,
            status=status,
        )

    async def update_status(self, order_id: int, status: str) -> DbOrder | None:
        return await self.orders.update_status(order_id=order_id, status=status)

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

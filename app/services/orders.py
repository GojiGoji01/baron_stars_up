from dataclasses import asdict, dataclass
from enum import StrEnum
from itertools import count
from typing import Any


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

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.repositories.orders import OrderStatus, OrdersRepository


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.orders = OrdersRepository(session)

    async def list_orders(
        self,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[Order]:
        orders = await self.orders.list_orders(
            limit=limit,
            offset=offset,
            status=status,
        )
        return list(orders)

    async def complete_order(self, order_id: int) -> Order | None:
        return await self.orders.update_status(order_id, OrderStatus.COMPLETED)

    async def mark_failed(self, order_id: int) -> Order | None:
        return await self.orders.update_status(order_id, OrderStatus.FAILED)

    async def refund_request(self, order_id: int) -> Order | None:
        return await self.orders.update_status(order_id, OrderStatus.REFUNDED)

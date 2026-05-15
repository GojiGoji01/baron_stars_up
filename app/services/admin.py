from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.repositories.orders import OrderStatus, OrdersRepository
from app.services.orders import OrdersService


class AdminService:
    def __init__(self, session_or_orders_service: AsyncSession | OrdersService) -> None:
        if isinstance(session_or_orders_service, OrdersService):
            self.orders_service = session_or_orders_service
            self.orders = session_or_orders_service.orders
        else:
            self.orders = OrdersRepository(session_or_orders_service)
            self.orders_service = OrdersService(session_or_orders_service)

    async def list_orders(
        self,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[Order]:
        return await self.orders_service.get_all_orders(
            limit=limit,
            offset=offset,
            status=status,
        )

    async def complete_order(self, order_id: int) -> Order | None:
        return await self.orders.update_status(order_id, OrderStatus.COMPLETED)

    async def mark_failed(self, order_id: int) -> Order | None:
        return await self.orders.update_status(order_id, OrderStatus.FAILED)

    async def refund_request(self, order_id: int) -> Order | None:
        return await self.orders.update_status(order_id, OrderStatus.REFUNDED)

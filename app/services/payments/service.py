from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.payment import Payment
from app.repositories.payments import PaymentStatus, PaymentsRepository


class PaymentsService:
    def __init__(self, session: AsyncSession) -> None:
        self.payments = PaymentsRepository(session)

    async def create_payment(
        self,
        order_id: int,
        provider: str,
        amount: Decimal,
        status: str = PaymentStatus.CREATED,
    ) -> Payment:
        return await self.payments.create_payment(
            order_id=order_id,
            provider=provider,
            amount=amount,
            status=status,
        )

    async def verify_payment(
        self,
        payment_id: int,
        is_successful: bool = True,
    ) -> Payment | None:
        status = PaymentStatus.PAID if is_successful else PaymentStatus.FAILED
        return await self.payments.update_status(payment_id=payment_id, status=status)

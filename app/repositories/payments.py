from collections.abc import Sequence
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.payment import Payment


class PaymentStatus(StrEnum):
    CREATED = "created"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_payment(
        self,
        order_id: int,
        provider: str,
        amount: Decimal,
        status: str = PaymentStatus.CREATED,
    ) -> Payment:
        payment = Payment(
            order_id=order_id,
            provider=provider,
            amount=amount,
            status=status,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_payment_by_id(self, payment_id: int) -> Payment | None:
        return await self.session.get(Payment, payment_id)

    async def update_payment(self, payment_id: int, **fields: Any) -> Payment | None:
        payment = await self.get_payment_by_id(payment_id)
        if payment is None:
            return None

        for field, value in fields.items():
            if hasattr(payment, field):
                setattr(payment, field, value)

        await self.session.flush()
        return payment

    async def update_status(self, payment_id: int, status: str) -> Payment | None:
        return await self.update_payment(payment_id, status=status)

    async def set_pending_payment(self, payment_id: int) -> Payment | None:
        return await self.update_status(payment_id, PaymentStatus.PENDING_PAYMENT)

    async def mark_paid(self, payment_id: int) -> Payment | None:
        return await self.update_status(payment_id, PaymentStatus.PAID)

    async def mark_completed(self, payment_id: int) -> Payment | None:
        return await self.update_status(payment_id, PaymentStatus.COMPLETED)

    async def mark_failed(self, payment_id: int) -> Payment | None:
        return await self.update_status(payment_id, PaymentStatus.FAILED)

    async def mark_refunded(self, payment_id: int) -> Payment | None:
        return await self.update_status(payment_id, PaymentStatus.REFUNDED)

    async def list_payments(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        provider: str | None = None,
    ) -> Sequence[Payment]:
        query = select(Payment).order_by(Payment.id.desc()).limit(limit).offset(offset)
        if status is not None:
            query = query.where(Payment.status == status)
        if provider is not None:
            query = query.where(Payment.provider == provider)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_payments_by_order(self, order_id: int) -> Sequence[Payment]:
        result = await self.session.execute(
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(Payment.id.desc())
        )
        return result.scalars().all()

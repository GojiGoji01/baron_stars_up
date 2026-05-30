from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.delivery_attempt import DeliveryAttempt


class DeliveryAttemptStatus(StrEnum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFICATION_REQUIRED = "verification_required"


class DeliveryAttemptsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_attempt(
        self,
        *,
        order_id: int,
        attempt_key: str,
        provider: str,
        status: str = DeliveryAttemptStatus.STARTED.value,
        external_transaction_id: str | None = None,
        error_message: str | None = None,
    ) -> DeliveryAttempt:
        attempt = DeliveryAttempt(
            order_id=order_id,
            attempt_key=attempt_key,
            provider=provider,
            status=status,
            external_transaction_id=external_transaction_id,
            error_message=error_message,
        )
        self.session.add(attempt)
        await self.session.flush()
        return attempt

    async def create_attempt_or_get(
        self,
        *,
        order_id: int,
        attempt_key: str,
        provider: str,
        status: str = DeliveryAttemptStatus.STARTED.value,
        external_transaction_id: str | None = None,
        error_message: str | None = None,
    ) -> tuple[DeliveryAttempt, bool]:
        existing_attempt = await self.get_by_attempt_key(attempt_key=attempt_key)
        if existing_attempt is not None:
            return existing_attempt, False

        attempt = DeliveryAttempt(
            order_id=order_id,
            attempt_key=attempt_key,
            provider=provider,
            status=status,
            external_transaction_id=external_transaction_id,
            error_message=error_message,
        )
        try:
            async with self.session.begin_nested():
                self.session.add(attempt)
                await self.session.flush()
            return attempt, True
        except IntegrityError:
            existing_attempt = await self.get_by_attempt_key(attempt_key=attempt_key)
            if existing_attempt is not None:
                return existing_attempt, False
            raise

    async def get_latest_for_order(self, *, order_id: int) -> DeliveryAttempt | None:
        result = await self.session.execute(
            select(DeliveryAttempt)
            .where(DeliveryAttempt.order_id == order_id)
            .order_by(DeliveryAttempt.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_attempt_key(self, *, attempt_key: str) -> DeliveryAttempt | None:
        result = await self.session.execute(
            select(DeliveryAttempt).where(DeliveryAttempt.attempt_key == attempt_key)
        )
        return result.scalar_one_or_none()

    async def update_attempt(
        self,
        attempt_id: int,
        *,
        status: str,
        external_transaction_id: str | None = None,
        error_message: str | None = None,
    ) -> DeliveryAttempt | None:
        attempt = await self.session.get(DeliveryAttempt, attempt_id)
        if attempt is None:
            return None

        attempt.status = status
        if external_transaction_id is not None:
            attempt.external_transaction_id = external_transaction_id
        attempt.error_message = error_message
        attempt.updated_at = datetime.utcnow()
        await self.session.flush()
        return attempt

    async def list_for_order(self, *, order_id: int) -> Sequence[DeliveryAttempt]:
        result = await self.session.execute(
            select(DeliveryAttempt)
            .where(DeliveryAttempt.order_id == order_id)
            .order_by(DeliveryAttempt.id.desc())
        )
        return result.scalars().all()

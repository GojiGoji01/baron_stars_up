from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.delivery_attempt import DeliveryAttempt
from app.repositories.delivery_attempts import DeliveryAttemptStatus, DeliveryAttemptsRepository


class DeliveryAttemptsService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = DeliveryAttemptsRepository(session)

    async def start_attempt(
        self,
        *,
        order_id: int,
        attempt_key: str,
        provider: str,
    ) -> DeliveryAttempt:
        return await self.repository.create_attempt(
            order_id=order_id,
            attempt_key=attempt_key,
            provider=provider,
            status=DeliveryAttemptStatus.STARTED.value,
        )

    async def start_attempt_or_get(
        self,
        *,
        order_id: int,
        attempt_key: str,
        provider: str,
    ) -> tuple[DeliveryAttempt, bool]:
        return await self.repository.create_attempt_or_get(
            order_id=order_id,
            attempt_key=attempt_key,
            provider=provider,
            status=DeliveryAttemptStatus.STARTED.value,
        )

    async def mark_completed(
        self,
        *,
        attempt_id: int,
        external_transaction_id: str | None,
    ) -> DeliveryAttempt | None:
        return await self.repository.update_attempt(
            attempt_id,
            status=DeliveryAttemptStatus.COMPLETED.value,
            external_transaction_id=external_transaction_id,
        )

    async def mark_failed(
        self,
        *,
        attempt_id: int,
        error_message: str | None,
    ) -> DeliveryAttempt | None:
        return await self.repository.update_attempt(
            attempt_id,
            status=DeliveryAttemptStatus.FAILED.value,
            error_message=error_message,
        )

    async def mark_verification_required(
        self,
        *,
        attempt_id: int,
        error_message: str | None,
        external_transaction_id: str | None = None,
    ) -> DeliveryAttempt | None:
        return await self.repository.update_attempt(
            attempt_id,
            status=DeliveryAttemptStatus.VERIFICATION_REQUIRED.value,
            external_transaction_id=external_transaction_id,
            error_message=error_message,
        )

    async def get_latest_for_order(self, *, order_id: int) -> DeliveryAttempt | None:
        return await self.repository.get_latest_for_order(order_id=order_id)

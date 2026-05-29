from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.referral_transaction import ReferralTransaction


class ReferralTransactionsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_referral_transaction(
        self,
        *,
        user_id: int,
        order_id: int,
        amount: Decimal,
        percent: Decimal,
        status: str,
    ) -> ReferralTransaction:
        transaction = ReferralTransaction(
            user_id=user_id,
            order_id=order_id,
            amount=amount,
            percent=percent,
            status=status,
        )
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def exists_referral_transaction_for_order(self, order_id: int) -> bool:
        result = await self.session.execute(
            select(ReferralTransaction.id).where(ReferralTransaction.order_id == order_id)
        )
        return result.scalar_one_or_none() is not None

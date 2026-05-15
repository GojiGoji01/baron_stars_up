from decimal import Decimal

from config import settings


class ReferralsService:
    def __init__(self) -> None:
        self.enabled = settings.referrals_enabled

    async def calculate_referral_profit(self, profit_amount: Decimal) -> Decimal:
        if not self.enabled:
            return Decimal("0.00")

        percent = Decimal(settings.referral_percent) / Decimal("100")
        return profit_amount * percent

    async def accrue_after_completed(self, user_id: int, order_id: int) -> None:
        return None

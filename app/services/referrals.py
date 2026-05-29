import logging
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.repositories.orders import OrdersRepository
from app.repositories.referral_transactions import ReferralTransactionsRepository
from app.repositories.users import UsersRepository
from config import settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReferralItem:
    telegram_id: int
    username: str | None
    earned_amount: Decimal
    completed_orders_count: int

    @property
    def is_active(self) -> bool:
        return self.completed_orders_count > 0


@dataclass(frozen=True)
class ReferralDashboard:
    referral_count: int
    active_referral_count: int
    without_purchase_count: int
    referral_balance: Decimal
    total_referral_earned: Decimal


@dataclass(frozen=True)
class ReferralPage:
    items: tuple[ReferralItem, ...]
    current_page: int
    total_pages: int
    total_items: int


class ReferralsService:
    def __init__(self, session: AsyncSession) -> None:
        self.enabled = settings.referrals_enabled
        self.session = session
        self.users = UsersRepository(session)
        self.orders = OrdersRepository(session)
        self.transactions = ReferralTransactionsRepository(session)

    async def calculate_referral_profit(self, profit_amount: Decimal) -> Decimal:
        if not self.enabled:
            return Decimal("0.00")

        percent = Decimal(settings.referral_percent) / Decimal("100")
        return (profit_amount * percent).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    async def accrue_after_completed(self, order: Order) -> None:
        if not self.enabled:
            logger.info(
                "referral_accrual_skipped order_id=%s reason=referrals_disabled",
                order.id,
            )
            return

        if order.id is None:
            logger.info("referral_accrual_skipped order_id=None reason=missing_order_id")
            return

        if await self.transactions.exists_referral_transaction_for_order(order.id):
            logger.info("referral_accrual_duplicate order_id=%s", order.id)
            return

        buyer = await self.users.get_user_by_telegram_id(order.user_id)
        if buyer is None:
            buyer = await self.users.get_or_create_user(telegram_id=order.user_id)

        if buyer.referred_by is None:
            logger.info(
                "referral_accrual_skipped order_id=%s user_id=%s reason=no_referrer",
                order.id,
                order.user_id,
            )
            return

        if settings.referral_base != "profit":
            logger.info(
                "referral_accrual_skipped order_id=%s reason=unsupported_referral_base base=%s",
                order.id,
                settings.referral_base,
            )
            return

        reward = await self.calculate_referral_profit(order.profit_amount)
        if reward <= Decimal("0.00"):
            logger.info(
                "referral_accrual_skipped order_id=%s reason=non_positive_reward reward=%s",
                order.id,
                reward,
            )
            return

        await self.users.increment_referral_balance(buyer.referred_by, reward)
        await self.transactions.create_referral_transaction(
            user_id=buyer.referred_by,
            order_id=order.id,
            amount=reward,
            percent=Decimal(settings.referral_percent),
            status="completed",
        )
        await self.orders.update_order(order.id, referral_profit=reward)
        logger.info(
            "referral_accrued order_id=%s buyer_user_id=%s referrer_user_id=%s reward=%s",
            order.id,
            order.user_id,
            buyer.referred_by,
            reward,
        )

    async def get_dashboard(self, referrer_id: int) -> ReferralDashboard:
        referrer = await self.users.get_or_create_user(telegram_id=referrer_id)
        referred_users = list(await self.users.list_referred_users(referred_by=referrer_id))
        buyer_ids = [user.telegram_id for user in referred_users]
        completed_counts_map = await self.orders.get_completed_order_counts_by_user_ids(buyer_ids)
        active_referral_count = sum(1 for user in referred_users if completed_counts_map.get(user.telegram_id, 0) > 0)

        return ReferralDashboard(
            referral_count=len(referred_users),
            active_referral_count=active_referral_count,
            without_purchase_count=len(referred_users) - active_referral_count,
            referral_balance=referrer.referral_balance,
            total_referral_earned=referrer.total_referral_earned,
        )

    async def get_referral_page(
        self,
        referrer_id: int,
        *,
        page: int = 1,
        page_size: int = 10,
    ) -> ReferralPage:
        referred_users = list(await self.users.list_referred_users(referred_by=referrer_id, limit=1000, offset=0))
        buyer_ids = [user.telegram_id for user in referred_users]
        earnings_map = await self.orders.get_referral_earnings_by_user_ids(buyer_ids)
        completed_counts_map = await self.orders.get_completed_order_counts_by_user_ids(buyer_ids)

        items = [
            ReferralItem(
                telegram_id=user.telegram_id,
                username=user.username,
                earned_amount=earnings_map.get(user.telegram_id, Decimal("0.00")),
                completed_orders_count=completed_counts_map.get(user.telegram_id, 0),
            )
            for user in referred_users
        ]

        total_items = len(items)
        total_pages = max(1, ceil(total_items / page_size)) if page_size > 0 else 1
        current_page = min(max(page, 1), total_pages)
        start_index = (current_page - 1) * page_size
        end_index = start_index + page_size

        return ReferralPage(
            items=tuple(items[start_index:end_index]),
            current_page=current_page,
            total_pages=total_pages,
            total_items=total_items,
        )

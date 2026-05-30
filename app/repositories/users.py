from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


class UsersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_user(
        self,
        telegram_id: int,
        username: str | None = None,
        referral_code: str | None = None,
        referred_by: int | None = None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            referral_code=referral_code,
            referred_by=referred_by,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_wallet_address(self, wallet_address: str) -> User | None:
        normalized_address = wallet_address.strip()
        if not normalized_address:
            return None

        result = await self.session.execute(
            select(User).where(User.wallet_address == normalized_address)
        )
        return result.scalar_one_or_none()

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None = None,
        referral_code: str | None = None,
        referred_by: int | None = None,
    ) -> User:
        user = await self.get_user_by_telegram_id(telegram_id)
        if user is not None:
            normalized_username = username or None
            if normalized_username is not None and user.username != normalized_username:
                user.username = normalized_username
                await self.session.flush()
            return user

        return await self.create_user(
            telegram_id=telegram_id,
            username=username,
            referral_code=referral_code,
            referred_by=referred_by,
        )

    async def update_user(self, user_id: int, **fields: Any) -> User | None:
        user = await self.get_user_by_id(user_id)
        if user is None:
            return None

        for field, value in fields.items():
            if hasattr(user, field):
                setattr(user, field, value)

        await self.session.flush()
        return user

    async def bind_wallet(
        self,
        *,
        telegram_id: int,
        wallet_address: str,
        wallet_provider: str,
    ) -> User | None:
        normalized_address = wallet_address.strip()
        normalized_provider = wallet_provider.strip().lower()
        if not normalized_address:
            raise ValueError("wallet_address is empty")
        if not normalized_provider:
            raise ValueError("wallet_provider is empty")

        owner = await self.get_user_by_wallet_address(normalized_address)
        if owner is not None and owner.telegram_id != telegram_id:
            raise ValueError("wallet address is already bound to another user")

        user = await self.get_user_by_telegram_id(telegram_id)
        if user is None:
            return None

        now = datetime.utcnow()
        user.wallet_address = normalized_address
        user.wallet_provider = normalized_provider
        user.wallet_status = "connected"
        user.wallet_connected_at = user.wallet_connected_at or now
        user.wallet_last_verified_at = now
        await self.session.flush()
        return user

    async def disconnect_wallet(self, *, telegram_id: int) -> User | None:
        user = await self.get_user_by_telegram_id(telegram_id)
        if user is None:
            return None

        user.wallet_status = "disconnected"
        user.wallet_address = None
        user.wallet_provider = None
        user.wallet_connected_at = None
        user.wallet_last_verified_at = None
        await self.session.flush()
        return user

    async def touch_wallet_verified_at(self, *, telegram_id: int) -> User | None:
        user = await self.get_user_by_telegram_id(telegram_id)
        if user is None or not user.wallet_address:
            return user

        user.wallet_last_verified_at = datetime.utcnow()
        await self.session.flush()
        return user

    async def set_referred_by_once(self, telegram_id: int, referred_by: int) -> User | None:
        user = await self.get_user_by_telegram_id(telegram_id)
        if user is None:
            return None

        if user.referred_by is not None:
            return user

        user.referred_by = referred_by
        await self.session.flush()
        return user

    async def increment_referral_balance(
        self,
        telegram_id: int,
        amount: Decimal,
    ) -> User:
        user = await self.get_or_create_user(telegram_id=telegram_id)
        user.referral_balance += amount
        user.total_referral_earned += amount
        await self.session.flush()
        return user

    async def list_users(self, limit: int = 100, offset: int = 0) -> Sequence[User]:
        result = await self.session.execute(
            select(User).order_by(User.id.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def list_referred_users(
        self,
        referred_by: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[User]:
        result = await self.session.execute(
            select(User)
            .where(User.referred_by == referred_by)
            .order_by(User.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user


UserRepository = UsersRepository

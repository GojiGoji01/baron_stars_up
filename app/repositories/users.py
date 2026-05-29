from collections.abc import Sequence
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

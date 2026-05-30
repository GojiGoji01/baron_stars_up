from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    referral_code: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    referred_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    referral_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    total_referral_earned: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    wallet_address: Mapped[str | None] = mapped_column(String(128), unique=True, index=True, nullable=True)
    wallet_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    wallet_status: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    wallet_connected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    wallet_last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

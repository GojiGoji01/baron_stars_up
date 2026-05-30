from decimal import Decimal
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    order_type: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    recipient: Mapped[str | None] = mapped_column(String(128), nullable=True)
    recipient_tg_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    gift_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    amount_rub: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_rub: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    profit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    referral_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    payment_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payment_transaction_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    payment_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    delivery_status: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    delivery_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fragment_transaction_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

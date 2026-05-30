from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FragmentBrowserSession(Base):
    __tablename__ = "fragment_browser_sessions"

    source: Mapped[str] = mapped_column(String(64), primary_key=True)
    cookies_base64: Mapped[str] = mapped_column(Text, nullable=False)
    local_storage_base64: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

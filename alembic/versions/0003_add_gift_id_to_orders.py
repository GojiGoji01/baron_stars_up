"""add gift id to orders

Revision ID: 0003_add_gift_id_to_orders
Revises: 0002_extend_orders_for_payments
Create Date: 2026-05-26 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0003_add_gift_id_to_orders"
down_revision: str | None = "0002_extend_orders_for_payments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("gift_id", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_orders_gift_id"), "orders", ["gift_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_gift_id"), table_name="orders")
    op.drop_column("orders", "gift_id")

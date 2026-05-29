"""extend orders for payments and delivery

Revision ID: 0002_extend_orders_for_payments
Revises: 0001_initial_tables
Create Date: 2026-05-25 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0002_extend_orders_for_payments"
down_revision: str | None = "0001_initial_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("order_id", sa.String(length=64), nullable=True))
    op.add_column("orders", sa.Column("order_type", sa.String(length=32), nullable=True))
    op.add_column("orders", sa.Column("recipient", sa.String(length=128), nullable=True))
    op.add_column("orders", sa.Column("recipient_tg_id", sa.BigInteger(), nullable=True))
    op.add_column("orders", sa.Column("amount", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("price_rub", sa.Numeric(12, 2), nullable=True))
    op.add_column("orders", sa.Column("payment_provider", sa.String(length=32), nullable=True))
    op.add_column("orders", sa.Column("payment_transaction_id", sa.String(length=128), nullable=True))
    op.add_column("orders", sa.Column("payment_url", sa.String(length=512), nullable=True))
    op.add_column("orders", sa.Column("delivery_status", sa.String(length=32), nullable=True))
    op.add_column(
        "orders",
        sa.Column("delivery_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("orders", sa.Column("fragment_transaction_id", sa.String(length=128), nullable=True))
    op.add_column(
        "orders",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.add_column(
        "orders",
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_orders_order_id"), "orders", ["order_id"], unique=True)
    op.create_index(op.f("ix_orders_order_type"), "orders", ["order_type"], unique=False)
    op.create_index(op.f("ix_orders_recipient_tg_id"), "orders", ["recipient_tg_id"], unique=False)
    op.create_index(
        op.f("ix_orders_payment_transaction_id"),
        "orders",
        ["payment_transaction_id"],
        unique=False,
    )
    op.create_index(op.f("ix_orders_delivery_status"), "orders", ["delivery_status"], unique=False)
    op.create_index(
        op.f("ix_orders_fragment_transaction_id"),
        "orders",
        ["fragment_transaction_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_fragment_transaction_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_delivery_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_payment_transaction_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_recipient_tg_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_type"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_id"), table_name="orders")
    op.drop_column("orders", "updated_at")
    op.drop_column("orders", "created_at")
    op.drop_column("orders", "fragment_transaction_id")
    op.drop_column("orders", "delivery_attempts")
    op.drop_column("orders", "delivery_status")
    op.drop_column("orders", "payment_url")
    op.drop_column("orders", "payment_transaction_id")
    op.drop_column("orders", "payment_provider")
    op.drop_column("orders", "price_rub")
    op.drop_column("orders", "amount")
    op.drop_column("orders", "recipient_tg_id")
    op.drop_column("orders", "recipient")
    op.drop_column("orders", "order_type")
    op.drop_column("orders", "order_id")

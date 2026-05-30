"""harden payments and wallets

Revision ID: 0006_harden_payments_and_wallets
Revises: 0005_fragment_sessions
Create Date: 2026-05-30 18:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0006_harden_payments_and_wallets"
down_revision: str | None = "0005_fragment_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("wallet_address", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("wallet_provider", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("wallet_status", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("wallet_connected_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("wallet_last_verified_at", sa.DateTime(), nullable=True))
    op.create_index("ix_users_wallet_address", "users", ["wallet_address"], unique=True)
    op.create_index("ix_users_wallet_status", "users", ["wallet_status"], unique=False)

    op.drop_index(op.f("ix_orders_payment_transaction_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_fragment_transaction_id"), table_name="orders")
    op.create_unique_constraint(
        "uq_orders_payment_transaction_id",
        "orders",
        ["payment_transaction_id"],
    )
    op.create_unique_constraint(
        "uq_orders_fragment_transaction_id",
        "orders",
        ["fragment_transaction_id"],
    )

    op.create_table(
        "delivery_attempts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("attempt_key", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("external_transaction_id", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_key"),
        sa.UniqueConstraint("external_transaction_id"),
    )
    op.create_index(op.f("ix_delivery_attempts_order_id"), "delivery_attempts", ["order_id"], unique=False)
    op.create_index(op.f("ix_delivery_attempts_attempt_key"), "delivery_attempts", ["attempt_key"], unique=True)
    op.create_index(op.f("ix_delivery_attempts_provider"), "delivery_attempts", ["provider"], unique=False)
    op.create_index(op.f("ix_delivery_attempts_status"), "delivery_attempts", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_delivery_attempts_status"), table_name="delivery_attempts")
    op.drop_index(op.f("ix_delivery_attempts_provider"), table_name="delivery_attempts")
    op.drop_index(op.f("ix_delivery_attempts_attempt_key"), table_name="delivery_attempts")
    op.drop_index(op.f("ix_delivery_attempts_order_id"), table_name="delivery_attempts")
    op.drop_table("delivery_attempts")

    op.drop_constraint("uq_orders_fragment_transaction_id", "orders", type_="unique")
    op.drop_constraint("uq_orders_payment_transaction_id", "orders", type_="unique")
    op.create_index(
        op.f("ix_orders_fragment_transaction_id"),
        "orders",
        ["fragment_transaction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_orders_payment_transaction_id"),
        "orders",
        ["payment_transaction_id"],
        unique=False,
    )

    op.drop_index("ix_users_wallet_status", table_name="users")
    op.drop_index("ix_users_wallet_address", table_name="users")
    op.drop_column("users", "wallet_last_verified_at")
    op.drop_column("users", "wallet_connected_at")
    op.drop_column("users", "wallet_status")
    op.drop_column("users", "wallet_provider")
    op.drop_column("users", "wallet_address")

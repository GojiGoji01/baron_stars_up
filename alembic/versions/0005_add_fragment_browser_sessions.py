"""add fragment browser sessions

Revision ID: 0005_fragment_sessions
Revises: 0004_add_username_to_users
Create Date: 2026-05-30 13:35:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0005_fragment_sessions"
down_revision: str | None = "0004_add_username_to_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fragment_browser_sessions",
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("cookies_base64", sa.Text(), nullable=False),
        sa.Column("local_storage_base64", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("source"),
    )


def downgrade() -> None:
    op.drop_table("fragment_browser_sessions")

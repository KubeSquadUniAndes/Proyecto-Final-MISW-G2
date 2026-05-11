"""Add booking_ids text[] column and parcial status to rooms

Revision ID: 0001
Revises:
Create Date: 2026-05-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'parcial' to the existing room_status_enum type.
    # IF NOT EXISTS prevents errors on a fresh DB where create_all already added it.
    op.execute("ALTER TYPE room_status_enum ADD VALUE IF NOT EXISTS 'parcial'")

    # Add booking_ids as a PostgreSQL text[] column defaulting to an empty array.
    op.add_column(
        "rooms",
        sa.Column(
            "booking_ids",
            sa.ARRAY(sa.String),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("rooms", "booking_ids")
    # PostgreSQL does not support removing enum values natively.
    # A full revert would require recreating the enum without 'parcial'.

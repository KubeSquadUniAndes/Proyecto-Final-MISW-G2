"""Add payment_status to bookings

Revision ID: 004_add_payment_status
Revises: 003_add_payment_id
Create Date: 2026-05-09 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "004_add_payment_status"
down_revision = "003_add_payment_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("payment_status", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bookings", "payment_status")

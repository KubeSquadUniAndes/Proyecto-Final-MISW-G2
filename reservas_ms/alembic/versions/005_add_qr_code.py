"""Add QR code fields to bookings

Revision ID: 005_add_qr_code
Revises: 004_add_payment_status
Create Date: 2026-05-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "005_add_qr_code"
down_revision = "004_add_payment_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("qr_code", sa.Text, nullable=True))
    op.add_column(
        "bookings",
        sa.Column("qr_generated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column(
            "qr_is_valid",
            sa.Boolean,
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("bookings", "qr_is_valid")
    op.drop_column("bookings", "qr_generated_at")
    op.drop_column("bookings", "qr_code")

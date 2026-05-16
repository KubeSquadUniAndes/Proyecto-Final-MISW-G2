"""Add check-in audit columns and checked_in status to bookings

Revision ID: 006_add_checkin_columns
Revises: 005_add_qr_code
Create Date: 2026-05-15 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "006_add_checkin_columns"
down_revision = "005_add_qr_code"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new enum value to booking_status_enum
    op.execute("ALTER TYPE booking_status_enum ADD VALUE IF NOT EXISTS 'checked_in'")

    # Add check-in audit columns
    op.add_column(
        "bookings",
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("checkin_staff_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("checkin_device", sa.String(255), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("checkin_ip", sa.String(45), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bookings", "checkin_ip")
    op.drop_column("bookings", "checkin_device")
    op.drop_column("bookings", "checkin_staff_id")
    op.drop_column("bookings", "checked_in_at")
    # Note: PostgreSQL does not support removing enum values.
    # The 'checked_in' value must be removed manually if needed.

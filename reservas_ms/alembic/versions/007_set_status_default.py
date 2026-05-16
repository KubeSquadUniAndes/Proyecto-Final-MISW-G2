"""Set DEFAULT on bookings.status column to avoid ::VARCHAR cast mismatch

Revision ID: 007_set_status_default
Revises: 006_add_checkin_columns
Create Date: 2026-05-16 00:00:00.000000

The ORM uses String(50) + server_default to keep SQLAlchemy's Enum machinery
out of the INSERT, but the column needs a real PostgreSQL DEFAULT so that
omitting status from the INSERT does not trigger a NOT NULL violation.
"""

from alembic import op

revision = "007_set_status_default"
down_revision = "006_add_checkin_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use untyped string literal — asyncpg mangles ::cast syntax even in DDL.
    # PostgreSQL implicitly coerces the string constant to booking_status_enum.
    op.execute("ALTER TABLE bookings ALTER COLUMN status SET DEFAULT 'pending'")


def downgrade() -> None:
    op.execute("ALTER TABLE bookings ALTER COLUMN status DROP DEFAULT")

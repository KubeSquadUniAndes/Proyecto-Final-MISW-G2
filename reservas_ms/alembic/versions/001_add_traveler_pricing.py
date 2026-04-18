"""add encrypted traveler fields and pricing

Revision ID: 001_add_traveler_pricing
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "001_add_traveler_pricing"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgcrypto extension for AES-256 encryption
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Booking identity
    op.add_column("bookings", sa.Column("booking_code", sa.String(15), nullable=True))
    op.create_unique_constraint("uq_bookings_booking_code", "bookings", ["booking_code"])
    op.create_index("ix_bookings_booking_code", "bookings", ["booking_code"])

    op.add_column("bookings", sa.Column("room_type", sa.String(100), nullable=True))
    op.add_column("bookings", sa.Column("num_guests", sa.Integer(), nullable=True, server_default="1"))
    op.add_column("bookings", sa.Column("additional_guests", sa.JSON(), nullable=True))
    op.add_column("bookings", sa.Column("special_requests", sa.Text(), nullable=True))

    # Pricing
    op.add_column("bookings", sa.Column("price_per_night", sa.Numeric(10, 2), nullable=True))
    op.add_column("bookings", sa.Column("total_nights", sa.Integer(), nullable=True))
    op.add_column("bookings", sa.Column("total_price", sa.Numeric(10, 2), nullable=True))
    op.add_column("bookings", sa.Column("taxes", sa.Numeric(10, 2), nullable=True))
    op.add_column("bookings", sa.Column("final_price", sa.Numeric(10, 2), nullable=True))

    # Sensitive fields — stored as bytea, encrypted with pgcrypto AES-256
    op.add_column("bookings", sa.Column("traveler_name", sa.LargeBinary(), nullable=True))
    op.add_column("bookings", sa.Column("traveler_email", sa.LargeBinary(), nullable=True))
    op.add_column("bookings", sa.Column("traveler_phone", sa.LargeBinary(), nullable=True))
    op.add_column("bookings", sa.Column("traveler_document", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column("bookings", "traveler_document")
    op.drop_column("bookings", "traveler_phone")
    op.drop_column("bookings", "traveler_email")
    op.drop_column("bookings", "traveler_name")
    op.drop_column("bookings", "final_price")
    op.drop_column("bookings", "taxes")
    op.drop_column("bookings", "total_price")
    op.drop_column("bookings", "total_nights")
    op.drop_column("bookings", "price_per_night")
    op.drop_column("bookings", "special_requests")
    op.drop_column("bookings", "additional_guests")
    op.drop_column("bookings", "num_guests")
    op.drop_column("bookings", "room_type")
    op.drop_index("ix_bookings_booking_code", table_name="bookings")
    op.drop_constraint("uq_bookings_booking_code", "bookings", type_="unique")
    op.drop_column("bookings", "booking_code")

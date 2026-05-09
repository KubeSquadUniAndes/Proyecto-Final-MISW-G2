"""Add payment_id to bookings

Revision ID: 003_add_payment_id
Revises: 002
Create Date: 2026-05-03 21:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_add_payment_id'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('bookings', sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_bookings_payment_id', 'bookings', ['payment_id'])


def downgrade() -> None:
    op.drop_index('ix_bookings_payment_id', table_name='bookings')
    op.drop_column('bookings', 'payment_id')

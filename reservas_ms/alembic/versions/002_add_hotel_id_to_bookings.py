"""add hotel_id to bookings

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001_add_traveler_pricing'
branch_labels = None
depends_on = None


def upgrade():
    # Add hotel_id column
    op.add_column('bookings', sa.Column('hotel_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Rename resource_id to room_id
    op.alter_column('bookings', 'resource_id', new_column_name='room_id')
    
    # Create index on hotel_id
    op.create_index(op.f('ix_bookings_hotel_id'), 'bookings', ['hotel_id'], unique=False)
    
    # Make hotel_id non-nullable after data migration
    # op.alter_column('bookings', 'hotel_id', nullable=False)


def downgrade():
    # Drop index
    op.drop_index(op.f('ix_bookings_hotel_id'), table_name='bookings')
    
    # Rename room_id back to resource_id
    op.alter_column('bookings', 'room_id', new_column_name='resource_id')
    
    # Drop hotel_id column
    op.drop_column('bookings', 'hotel_id')

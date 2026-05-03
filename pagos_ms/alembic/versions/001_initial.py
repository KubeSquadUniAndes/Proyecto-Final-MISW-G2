"""Initial payment table with pgcrypto

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgcrypto extension
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    
    # Create payment_provider_enum
    op.execute("""
        CREATE TYPE payment_provider_enum AS ENUM (
            'stripe', 'paypal', 'mercadopago', 'mock'
        )
    """)
    
    # Create payment_method_enum
    op.execute("""
        CREATE TYPE payment_method_enum AS ENUM (
            'credit_card', 'debit_card', 'paypal', 'bank_transfer'
        )
    """)
    
    # Create payment_status_enum
    op.execute("""
        CREATE TYPE payment_status_enum AS ENUM (
            'pending', 'processing', 'confirmed', 'failed', 'refunded'
        )
    """)
    
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('payment_provider', sa.Enum('stripe', 'paypal', 'mercadopago', 'mock', name='payment_provider_enum'), nullable=False),
        sa.Column('payment_method', sa.Enum('credit_card', 'debit_card', 'paypal', 'bank_transfer', name='payment_method_enum'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'confirmed', 'failed', 'refunded', name='payment_status_enum'), nullable=False),
        sa.Column('provider_transaction_id', sa.String(255), nullable=True, index=True),
        sa.Column('card_last_four', sa.String(4), nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, default=0),
        sa.Column('payment_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cardholder_name', sa.LargeBinary, nullable=True),
        sa.Column('cardholder_email', sa.LargeBinary, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('payments')
    op.execute('DROP TYPE IF EXISTS payment_status_enum')
    op.execute('DROP TYPE IF EXISTS payment_method_enum')
    op.execute('DROP TYPE IF EXISTS payment_provider_enum')

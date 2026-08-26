"""create_portfolio_transactions_table

Revision ID: c36dce8892eb
Revises: b25cbe9991da
Create Date: 2026-08-25 21:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c36dce8892eb'
down_revision: Union[str, Sequence[str], None] = 'b25cbe9991da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'portfolio_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('holding_id', sa.Integer(), nullable=True),
        sa.Column('asset_type', sa.String(length=30), nullable=False),
        sa.Column('asset_name', sa.String(length=200), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=True),
        sa.Column('isin', sa.String(length=20), nullable=True),
        sa.Column('transaction_type', sa.String(length=30), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('price', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('gross_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('fees', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('taxes', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('net_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=30), nullable=False, server_default='MANUAL'),
        sa.Column('external_reference', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['holding_id'], ['investment_holdings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'external_reference', name='uq_user_external_ref')
    )
    op.create_index(op.f('ix_portfolio_transactions_id'), 'portfolio_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_portfolio_transactions_user_id'), 'portfolio_transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_portfolio_transactions_holding_id'), 'portfolio_transactions', ['holding_id'], unique=False)
    op.create_index(op.f('ix_portfolio_transactions_symbol'), 'portfolio_transactions', ['symbol'], unique=False)
    op.create_index(op.f('ix_portfolio_transactions_isin'), 'portfolio_transactions', ['isin'], unique=False)
    op.create_index(op.f('ix_portfolio_transactions_transaction_type'), 'portfolio_transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_portfolio_transactions_transaction_date'), 'portfolio_transactions', ['transaction_date'], unique=False)
    op.create_index(op.f('ix_portfolio_transactions_external_reference'), 'portfolio_transactions', ['external_reference'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_portfolio_transactions_external_reference'), table_name='portfolio_transactions')
    op.drop_index(op.f('ix_portfolio_transactions_transaction_date'), table_name='portfolio_transactions')
    op.drop_index(op.f('ix_portfolio_transactions_transaction_type'), table_name='portfolio_transactions')
    op.drop_index(op.f('ix_portfolio_transactions_isin'), table_name='portfolio_transactions')
    op.drop_index(op.f('ix_portfolio_transactions_symbol'), table_name='portfolio_transactions')
    op.drop_index(op.f('ix_portfolio_transactions_holding_id'), table_name='portfolio_transactions')
    op.drop_index(op.f('ix_portfolio_transactions_user_id'), table_name='portfolio_transactions')
    op.drop_index(op.f('ix_portfolio_transactions_id'), table_name='portfolio_transactions')
    op.drop_table('portfolio_transactions')

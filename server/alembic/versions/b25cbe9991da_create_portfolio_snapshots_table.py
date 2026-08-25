"""create_portfolio_snapshots_table

Revision ID: b25cbe9991da
Revises: a23b3f7f0c45
Create Date: 2026-08-25 15:03:16.457101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b25cbe9991da'
down_revision: Union[str, Sequence[str], None] = 'a23b3f7f0c45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('market_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('invested_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('pnl', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('pnl_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'snapshot_date', name='uq_user_portfolio_snapshot_date')
    )
    op.create_index(op.f('ix_portfolio_snapshots_id'), 'portfolio_snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_portfolio_snapshots_user_id'), 'portfolio_snapshots', ['user_id'], unique=False)
    op.create_index(op.f('ix_portfolio_snapshots_snapshot_date'), 'portfolio_snapshots', ['snapshot_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_portfolio_snapshots_snapshot_date'), table_name='portfolio_snapshots')
    op.drop_index(op.f('ix_portfolio_snapshots_user_id'), table_name='portfolio_snapshots')
    op.drop_index(op.f('ix_portfolio_snapshots_id'), table_name='portfolio_snapshots')
    op.drop_table('portfolio_snapshots')

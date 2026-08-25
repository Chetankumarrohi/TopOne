"""add fund health scoring fields

Revision ID: a23b3f7f0c45
Revises: 10e83815625c
Create Date: 2026-08-10 17:53:57.636207
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a23b3f7f0c45"
down_revision: Union[str, Sequence[str], None] = "10e83815625c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add fund health scoring fields."""

    op.add_column(
        "investment_products",
        sa.Column("fund_health_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("consistency_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("rolling_return_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("risk_adjusted_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("downside_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("volatility_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("momentum_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("long_term_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("data_quality_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("peer_percentile", sa.Float(), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("fund_status", sa.String(50), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("fund_health_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "investment_products",
        sa.Column("health_calculated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Remove fund health scoring fields."""

    op.drop_column("investment_products", "health_calculated_at")
    op.drop_column("investment_products", "fund_health_summary")
    op.drop_column("investment_products", "fund_status")
    op.drop_column("investment_products", "peer_percentile")
    op.drop_column("investment_products", "data_quality_score")
    op.drop_column("investment_products", "long_term_score")
    op.drop_column("investment_products", "momentum_score")
    op.drop_column("investment_products", "volatility_score")
    op.drop_column("investment_products", "downside_score")
    op.drop_column("investment_products", "risk_adjusted_score")
    op.drop_column("investment_products", "rolling_return_score")
    op.drop_column("investment_products", "consistency_score")
    op.drop_column("investment_products", "fund_health_score")

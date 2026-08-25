"""expand investment product fund data

Revision ID: 3512b0e0680c
Revises: 0860641cc6a9
Create Date: 2026-08-09 15:59:15.951957
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3512b0e0680c"
down_revision: Union[str, Sequence[str], None] = "0860641cc6a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add detailed mutual-fund/product data fields.

    This migration intentionally modifies only
    investment_products.
    """

    op.add_column(
        "investment_products",
        sa.Column(
            "scheme_code",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "plan_type",
            sa.String(length=30),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "option_type",
            sa.String(length=30),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "riskometer",
            sa.String(length=50),
            nullable=True,
        ),
    )

    # NAV information
    op.add_column(
        "investment_products",
        sa.Column(
            "nav_date",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "previous_nav",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "daily_change",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "daily_change_percentage",
            sa.Float(),
            nullable=True,
        ),
    )

    # Fund information
    op.add_column(
        "investment_products",
        sa.Column(
            "aum",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "exit_load",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "benchmark",
            sa.String(length=150),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "launch_date",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "fund_manager",
            sa.String(length=200),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "investment_objective",
            sa.Text(),
            nullable=True,
        ),
    )

    # Returns
    op.add_column(
        "investment_products",
        sa.Column(
            "return_1d",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "return_1m",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "return_3m",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "return_6m",
            sa.Float(),
            nullable=True,
        ),
    )

    # Risk metrics
    op.add_column(
        "investment_products",
        sa.Column(
            "alpha",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "beta",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "sharpe_ratio",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "standard_deviation",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "portfolio_turnover",
            sa.Float(),
            nullable=True,
        ),
    )

    # Asset allocation
    op.add_column(
        "investment_products",
        sa.Column(
            "equity_percentage",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "debt_percentage",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "cash_percentage",
            sa.Float(),
            nullable=True,
        ),
    )

    # Market-cap allocation
    op.add_column(
        "investment_products",
        sa.Column(
            "large_cap_percentage",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "mid_cap_percentage",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "small_cap_percentage",
            sa.Float(),
            nullable=True,
        ),
    )

    # Data freshness
    op.add_column(
        "investment_products",
        sa.Column(
            "holdings_as_of",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        "investment_products",
        sa.Column(
            "data_updated_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f(
            "ix_investment_products_scheme_code"
        ),
        "investment_products",
        ["scheme_code"],
        unique=True,
    )


def downgrade() -> None:
    """
    Remove detailed fund-data fields.
    """

    op.drop_index(
        op.f(
            "ix_investment_products_scheme_code"
        ),
        table_name="investment_products",
    )

    op.drop_column(
        "investment_products",
        "data_updated_at",
    )

    op.drop_column(
        "investment_products",
        "holdings_as_of",
    )

    op.drop_column(
        "investment_products",
        "small_cap_percentage",
    )

    op.drop_column(
        "investment_products",
        "mid_cap_percentage",
    )

    op.drop_column(
        "investment_products",
        "large_cap_percentage",
    )

    op.drop_column(
        "investment_products",
        "cash_percentage",
    )

    op.drop_column(
        "investment_products",
        "debt_percentage",
    )

    op.drop_column(
        "investment_products",
        "equity_percentage",
    )

    op.drop_column(
        "investment_products",
        "portfolio_turnover",
    )

    op.drop_column(
        "investment_products",
        "standard_deviation",
    )

    op.drop_column(
        "investment_products",
        "sharpe_ratio",
    )

    op.drop_column(
        "investment_products",
        "beta",
    )

    op.drop_column(
        "investment_products",
        "alpha",
    )

    op.drop_column(
        "investment_products",
        "return_6m",
    )

    op.drop_column(
        "investment_products",
        "return_3m",
    )

    op.drop_column(
        "investment_products",
        "return_1m",
    )

    op.drop_column(
        "investment_products",
        "return_1d",
    )

    op.drop_column(
        "investment_products",
        "investment_objective",
    )

    op.drop_column(
        "investment_products",
        "fund_manager",
    )

    op.drop_column(
        "investment_products",
        "launch_date",
    )

    op.drop_column(
        "investment_products",
        "benchmark",
    )

    op.drop_column(
        "investment_products",
        "exit_load",
    )

    op.drop_column(
        "investment_products",
        "aum",
    )

    op.drop_column(
        "investment_products",
        "daily_change_percentage",
    )

    op.drop_column(
        "investment_products",
        "daily_change",
    )

    op.drop_column(
        "investment_products",
        "previous_nav",
    )

    op.drop_column(
        "investment_products",
        "nav_date",
    )

    op.drop_column(
        "investment_products",
        "riskometer",
    )

    op.drop_column(
        "investment_products",
        "option_type",
    )

    op.drop_column(
        "investment_products",
        "plan_type",
    )

    op.drop_column(
        "investment_products",
        "scheme_code",
    )
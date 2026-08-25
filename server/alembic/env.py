"""add fund nav history

Revision ID: 21f4ef1272ad
Revises: 3512b0e0680c
Create Date: 2026-08-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "21f4ef1272ad"
down_revision: Union[str, Sequence[str], None] = "3512b0e0680c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fund_nav_history",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "product_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "nav_date",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "nav",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "daily_change",
            sa.Float(),
            nullable=True,
        ),

        sa.Column(
            "daily_change_percentage",
            sa.Float(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
        ),

        sa.ForeignKeyConstraint(
            ["product_id"],
            ["investment_products.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.UniqueConstraint(
            "product_id",
            "nav_date",
            name="uq_fund_nav_product_date",
        ),
    )

    op.create_index(
        op.f(
            "ix_fund_nav_history_id"
        ),
        "fund_nav_history",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_fund_nav_history_product_id"
        ),
        "fund_nav_history",
        ["product_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_fund_nav_history_nav_date"
        ),
        "fund_nav_history",
        ["nav_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_fund_nav_history_nav_date"
        ),
        table_name="fund_nav_history",
    )

    op.drop_index(
        op.f(
            "ix_fund_nav_history_product_id"
        ),
        table_name="fund_nav_history",
    )

    op.drop_index(
        op.f(
            "ix_fund_nav_history_id"
        ),
        table_name="fund_nav_history",
    )

    op.drop_table(
        "fund_nav_history"
    )
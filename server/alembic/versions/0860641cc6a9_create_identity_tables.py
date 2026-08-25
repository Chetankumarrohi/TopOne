"""create identity tables

Revision ID: 0860641cc6a9
Revises: bdf567c6d84c
Create Date: 2026-08-04 00:09:32.276971
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0860641cc6a9"
down_revision: Union[str, Sequence[str], None] = "bdf567c6d84c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "financial_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("annual_income", sa.Float()),
        sa.Column("monthly_income", sa.Float()),
        sa.Column("monthly_expenses", sa.Float()),
        sa.Column("total_savings", sa.Float()),
        sa.Column("emergency_fund", sa.Float()),
        sa.Column("total_assets", sa.Float()),
        sa.Column("total_liabilities", sa.Float()),
        sa.Column("net_worth", sa.Float()),
        sa.Column("existing_investments", sa.Float()),
        sa.Column("insurance_cover", sa.Float()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "investment_goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("goal_name", sa.String(length=100), nullable=False),
        sa.Column("target_amount", sa.Float()),
        sa.Column("current_amount", sa.Float()),
        sa.Column("target_year", sa.Integer()),
        sa.Column("priority", sa.Integer()),
        sa.Column("status", sa.String(length=30)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
    )

    op.create_table(
        "risk_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("risk_tolerance", sa.String(length=50)),
        sa.Column("investment_experience", sa.String(length=50)),
        sa.Column("investment_horizon", sa.Integer()),
        sa.Column("liquidity_preference", sa.String(length=50)),
        sa.Column("age_score", sa.Float()),
        sa.Column("income_score", sa.Float()),
        sa.Column("goal_score", sa.Float()),
        sa.Column("final_risk_score", sa.Float()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=20)),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("gender", sa.String(length=20)),
        sa.Column("city", sa.String(length=100)),
        sa.Column("state", sa.String(length=100)),
        sa.Column("country", sa.String(length=100)),
        sa.Column("occupation", sa.String(length=150)),
        sa.Column("marital_status", sa.String(length=50)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "wealth_dna",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("financial_health_score", sa.Float()),
        sa.Column("savings_score", sa.Float()),
        sa.Column("investment_score", sa.Float()),
        sa.Column("diversification_score", sa.Float()),
        sa.Column("tax_efficiency_score", sa.Float()),
        sa.Column("retirement_score", sa.Float()),
        sa.Column("emergency_score", sa.Float()),
        sa.Column("overall_score", sa.Float()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("wealth_dna")
    op.drop_table("user_profiles")
    op.drop_table("risk_profiles")
    op.drop_table("investment_goals")
    op.drop_table("financial_profiles")
from sqlalchemy import (
    Column,
    Integer,
    Float,
    ForeignKey,
    DateTime,
    func,
)

from sqlalchemy.orm import relationship

from app.core.database import Base


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # -----------------------------
    # User-provided financial data
    # -----------------------------

    annual_income = Column(
        Float,
        default=0,
        nullable=False,
    )

    monthly_income = Column(
        Float,
        default=0,
        nullable=False,
    )

    monthly_expenses = Column(
        Float,
        default=0,
        nullable=False,
    )

    monthly_debt_payment = Column(
        Float,
        default=0,
        nullable=False,
    )

    total_savings = Column(
        Float,
        default=0,
        nullable=False,
    )

    emergency_fund = Column(
        Float,
        default=0,
        nullable=False,
    )

    total_assets = Column(
        Float,
        default=0,
        nullable=False,
    )

    total_liabilities = Column(
        Float,
        default=0,
        nullable=False,
    )

    existing_investments = Column(
        Float,
        default=0,
        nullable=False,
    )

    insurance_cover = Column(
        Float,
        default=0,
        nullable=False,
    )

    # -----------------------------
    # Backend-calculated fields
    # -----------------------------

    net_worth = Column(
        Float,
        default=0,
        nullable=False,
    )

    savings_rate = Column(
        Float,
        default=0,
        nullable=False,
    )

    debt_to_income_ratio = Column(
        Float,
        default=0,
        nullable=False,
    )

    emergency_months = Column(
        Float,
        default=0,
        nullable=False,
    )

    investment_ratio = Column(
        Float,
        default=0,
        nullable=False,
    )

    # -----------------------------
    # Timestamps
    # -----------------------------

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # -----------------------------
    # Relationship
    # -----------------------------

    user = relationship(
        "User",
        back_populates="financial_profile",
    )
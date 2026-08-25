from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.core.database import Base
from app.common.mixins import TimestampMixin


class WealthDNA(Base, TimestampMixin):
    __tablename__ = "wealth_dna"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )

    # Main Wealth DNA score
    wealth_score = Column(
        Float,
        nullable=False,
        default=0,
    )

    investor_personality = Column(
        String(100),
        nullable=False,
        default="Developing Investor",
    )

    # Wealth DNA dimensions
    financial_stability_score = Column(
        Float,
        nullable=False,
        default=0,
    )

    savings_discipline_score = Column(
        Float,
        nullable=False,
        default=0,
    )

    debt_health_score = Column(
        Float,
        nullable=False,
        default=0,
    )

    emergency_preparedness_score = Column(
        Float,
        nullable=False,
        default=0,
    )

    investment_readiness_score = Column(
        Float,
        nullable=False,
        default=0,
    )

    goal_readiness_score = Column(
        Float,
        nullable=False,
        default=0,
    )

    risk_alignment_score = Column(
        Float,
        nullable=False,
        default=0,
    )

    # Analysis
    strongest_trait = Column(
        String(100),
        nullable=True,
    )

    improvement_area = Column(
        String(100),
        nullable=True,
    )

    scoring_version = Column(
        String(20),
        nullable=False,
        default="wealth-v1.0",
    )

    user = relationship(
        "User",
        back_populates="wealth_dna",
    )
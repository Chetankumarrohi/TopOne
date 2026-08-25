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


class RiskProfile(Base, TimestampMixin):
    __tablename__ = "risk_profiles"

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

    # --------------------------------
    # Risk dimensions
    # --------------------------------

    capacity_score = Column(
        Float,
        default=0,
        nullable=False,
    )

    behaviour_score = Column(
        Float,
        default=0,
        nullable=False,
    )

    horizon_score = Column(
        Float,
        default=0,
        nullable=False,
    )

    experience_score = Column(
        Float,
        default=0,
        nullable=False,
    )

    liquidity_score = Column(
        Float,
        default=0,
        nullable=False,
    )

    # --------------------------------
    # Final result
    # --------------------------------

    final_risk_score = Column(
        Float,
        default=0,
        nullable=False,
    )

    risk_category = Column(
        String(30),
        nullable=False,
        default="Moderate",
    )

    # Conservative / Moderate / Aggressive

    recommended_equity_min = Column(
        Float,
        default=0,
        nullable=False,
    )

    recommended_equity_max = Column(
        Float,
        default=0,
        nullable=False,
    )

    # --------------------------------
    # Scoring version
    # --------------------------------

    scoring_version = Column(
        String(20),
        default="risk-v1.0",
        nullable=False,
    )

    # --------------------------------
    # Relationship
    # --------------------------------

    user = relationship(
        "User",
        back_populates="risk_profile",
    )

    answers = relationship(
        "RiskAnswer",
        back_populates="risk_profile",
        cascade="all, delete-orphan",
    )
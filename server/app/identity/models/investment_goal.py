from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Date,
)

from sqlalchemy.orm import relationship

from app.core.database import Base
from app.common.mixins import TimestampMixin


class InvestmentGoal(Base, TimestampMixin):
    __tablename__ = "investment_goals"

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
        nullable=False,
        index=True,
    )

    # --------------------------------
    # Goal information
    # --------------------------------

    goal_name = Column(
        String(100),
        nullable=False,
    )

    goal_type = Column(
        String(50),
        nullable=False,
        default="CUSTOM",
    )

    # Examples:
    # HOUSE
    # CAR
    # RETIREMENT
    # EDUCATION
    # WEDDING
    # TRAVEL
    # EMERGENCY_FUND
    # CUSTOM

    target_amount = Column(
        Float,
        nullable=False,
        default=0,
    )

    current_amount = Column(
        Float,
        nullable=False,
        default=0,
    )

    target_date = Column(
        Date,
        nullable=False,
    )

    # --------------------------------
    # Investment plan
    # --------------------------------

    monthly_contribution = Column(
        Float,
        nullable=False,
        default=0,
    )

    priority = Column(
        Integer,
        nullable=False,
        default=3,
    )

    # Priority:
    # 1 = Highest
    # 5 = Lowest

    # --------------------------------
    # Calculated goal metrics
    # --------------------------------

    progress_percentage = Column(
        Float,
        nullable=False,
        default=0,
    )

    required_monthly_investment = Column(
        Float,
        nullable=False,
        default=0,
    )

    months_remaining = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # --------------------------------
    # Goal status
    # --------------------------------

    status = Column(
        String(30),
        nullable=False,
        default="ACTIVE",
    )

    # ACTIVE
    # COMPLETED
    # PAUSED
    # CANCELLED

    user = relationship(
        "User",
        back_populates="goals",
    )
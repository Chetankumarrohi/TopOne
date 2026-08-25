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


class RiskAnswer(Base, TimestampMixin):
    __tablename__ = "risk_answers"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    risk_profile_id = Column(
        Integer,
        ForeignKey(
            "risk_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question_code = Column(
        String(50),
        nullable=False,
    )

    answer_value = Column(
        String(100),
        nullable=False,
    )

    score_awarded = Column(
        Float,
        default=0,
        nullable=False,
    )

    risk_profile = relationship(
        "RiskProfile",
        back_populates="answers",
    )
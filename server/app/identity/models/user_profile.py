from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.common.mixins import TimestampMixin


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    phone = Column(String(20))

    date_of_birth = Column(Date)

    gender = Column(String(20))

    city = Column(String(100))

    state = Column(String(100))

    country = Column(String(100))

    occupation = Column(String(150))

    marital_status = Column(String(50))

    user = relationship(
        "User",
        back_populates="profile",
    )
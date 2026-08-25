from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)

from app.core.database import Base
from app.common.mixins import TimestampMixin


class FundPipelineLock(
    Base,
    TimestampMixin,
):
    __tablename__ = "fund_pipeline_locks"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    lock_name = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    acquired_at = Column(
        DateTime,
        nullable=True,
    )

    owner = Column(
        String(200),
        nullable=True,
    )

    expires_at = Column(
        DateTime,
        nullable=True,
    )
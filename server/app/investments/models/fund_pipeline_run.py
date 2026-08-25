from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
)

from app.core.database import Base
from app.common.mixins import TimestampMixin


class FundPipelineRun(
    Base,
    TimestampMixin,
):
    __tablename__ = "fund_pipeline_runs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    pipeline_name = Column(
        String(100),
        nullable=False,
        default="DAILY_FUND_PIPELINE",
        index=True,
    )

    status = Column(
        String(30),
        nullable=False,
        default="RUNNING",
        index=True,
    )

    started_at = Column(
        DateTime,
        nullable=False,
    )

    finished_at = Column(
        DateTime,
        nullable=True,
    )

    duration_seconds = Column(
        Float,
        nullable=True,
    )

    failed_step = Column(
        String(100),
        nullable=True,
    )

    result_json = Column(
        Text,
        nullable=True,
    )

    error_message = Column(
        Text,
        nullable=True,
    )
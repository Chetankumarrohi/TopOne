from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
)

from app.core.database import Base
from app.common.mixins import TimestampMixin


class FundDataSyncRun(
    Base,
    TimestampMixin,
):
    __tablename__ = (
        "fund_data_sync_runs"
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # =====================================================
    # PIPELINE IDENTITY
    # =====================================================

    pipeline_name = Column(
        String(100),
        nullable=False,
        index=True,
    )

    source_name = Column(
        String(100),
        nullable=True,
        index=True,
    )

    source_type = Column(
        String(50),
        nullable=True,
        index=True,
    )

    provider_key = Column(
        String(100),
        nullable=True,
        index=True,
    )

    # =====================================================
    # EXECUTION STATUS
    # =====================================================

    status = Column(
        String(30),
        nullable=False,
        index=True,
    )

    started_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    completed_at = Column(
        DateTime,
        nullable=True,
    )

    duration_seconds = Column(
        Integer,
        nullable=True,
    )

    # =====================================================
    # RESULT COUNTS
    # =====================================================

    records_received = Column(
        Integer,
        nullable=True,
    )

    records_processed = Column(
        Integer,
        nullable=True,
    )

    records_created = Column(
        Integer,
        nullable=True,
    )

    records_updated = Column(
        Integer,
        nullable=True,
    )

    records_failed = Column(
        Integer,
        nullable=True,
    )

    records_unmatched = Column(
        Integer,
        nullable=True,
    )

    # =====================================================
    # SOURCE / FRESHNESS
    # =====================================================

    source_url = Column(
        Text,
        nullable=True,
    )

    source_period = Column(
        String(50),
        nullable=True,
    )

    latest_data_date = Column(
        DateTime,
        nullable=True,
    )

    # =====================================================
    # ERROR / DEBUG INFORMATION
    # =====================================================

    error_type = Column(
        String(100),
        nullable=True,
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    result_json = Column(
        Text,
        nullable=True,
    )

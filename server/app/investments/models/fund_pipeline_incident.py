from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)

from sqlalchemy.sql import func

from app.core.database import Base


class FundPipelineIncident(Base):
    __tablename__ = "fund_pipeline_incidents"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    incident_code = Column(
        String(100),
        nullable=False,
        index=True,
    )

    severity = Column(
        String(20),
        nullable=False,
    )

    status = Column(
        String(20),
        nullable=False,
        default="OPEN",
        index=True,
    )

    message = Column(
        Text,
        nullable=False,
    )

    first_detected_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    last_detected_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    resolved_at = Column(
        DateTime,
        nullable=True,
    )

    acknowledged = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    acknowledged_at = Column(
        DateTime,
        nullable=True,
    )

    acknowledged_by_user_id = Column(
        Integer,
        nullable=True,
    )

    alert_sent = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    alert_sent_at = Column(
        DateTime,
        nullable=True,
    )

    details_json = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
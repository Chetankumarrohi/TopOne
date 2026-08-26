from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Date,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
)

from sqlalchemy.orm import relationship

from app.core.database import Base
from app.common.mixins import TimestampMixin


class FundHealthHistory(Base, TimestampMixin):
    """
    Daily historical snapshot of TopOne Fund Health.

    One row per product per UTC calendar day.

    Purpose:
    - Fund Radar status timeline
    - historical health-score chart
    - status transition analysis
    - future ML features
    """

    __tablename__ = "fund_health_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey(
            "investment_products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    snapshot_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    calculated_at = Column(
        DateTime,
        nullable=False,
    )

    fund_health_score = Column(
        Float,
        nullable=True,
    )

    fund_status = Column(
        String(30),
        nullable=False,
        index=True,
    )

    history_days = Column(
        Integer,
        nullable=False,
        default=0,
    )

    data_quality_score = Column(
        Float,
        nullable=True,
    )

    long_term_score = Column(
        Float,
        nullable=True,
    )

    consistency_score = Column(
        Float,
        nullable=True,
    )

    risk_adjusted_score = Column(
        Float,
        nullable=True,
    )

    downside_score = Column(
        Float,
        nullable=True,
    )

    volatility_score = Column(
        Float,
        nullable=True,
    )

    momentum_score = Column(
        Float,
        nullable=True,
    )

    peer_percentile = Column(
        Float,
        nullable=True,
    )

    quality_score = Column(
        Float,
        nullable=True,
    )

    fundamental_score = Column(
        Float,
        nullable=True,
    )

    news_score = Column(
        Float,
        nullable=True,
    )

    fund_health_summary = Column(
        Text,
        nullable=True,
    )

    product = relationship(
        "InvestmentProduct",
    )

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "snapshot_date",
            name="uq_fund_health_history_product_date",
        ),
        Index(
            "ix_fund_health_history_product_date",
            "product_id",
            "snapshot_date",
        ),
        Index(
            "ix_fund_health_history_status_date",
            "fund_status",
            "snapshot_date",
        ),
    )

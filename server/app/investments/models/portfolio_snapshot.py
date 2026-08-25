from datetime import date, datetime, timezone

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

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

    snapshot_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    market_value = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    invested_value = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    pnl = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    pnl_percentage = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="portfolio_snapshots",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "snapshot_date",
            name="uq_user_portfolio_snapshot_date",
        ),
    )

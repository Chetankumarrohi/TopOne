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


class InvestmentHolding(Base, TimestampMixin):
    __tablename__ = "investment_holdings"

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
    # Asset identity
    # --------------------------------

    asset_type = Column(
        String(30),
        nullable=False,
    )

    # MUTUAL_FUND
    # STOCK
    # ETF
    # GOLD
    # BOND
    # PPF
    # EPF
    # NPS
    # CASH
    # OTHER

    asset_name = Column(
        String(200),
        nullable=False,
    )

    symbol = Column(
        String(50),
        nullable=True,
        index=True,
    )

    isin = Column(
        String(20),
        nullable=True,
        index=True,
    )

    provider = Column(
        String(100),
        nullable=True,
    )

    folio_number_masked = Column(
        String(50),
        nullable=True,
    )

    # --------------------------------
    # Holding data
    # --------------------------------

    quantity = Column(
        Float,
        nullable=False,
        default=0,
    )

    average_buy_price = Column(
        Float,
        nullable=False,
        default=0,
    )

    invested_amount = Column(
        Float,
        nullable=False,
        default=0,
    )

    current_price = Column(
        Float,
        nullable=False,
        default=0,
    )

    current_value = Column(
        Float,
        nullable=False,
        default=0,
    )

    # --------------------------------
    # Performance
    # --------------------------------

    total_gain = Column(
        Float,
        nullable=False,
        default=0,
    )

    total_gain_percentage = Column(
        Float,
        nullable=False,
        default=0,
    )

    # --------------------------------
    # Classification
    # --------------------------------

    asset_class = Column(
        String(50),
        nullable=True,
    )

    # EQUITY
    # DEBT
    # GOLD
    # CASH
    # HYBRID
    # OTHER

    category = Column(
        String(100),
        nullable=True,
    )

    sector = Column(
        String(100),
        nullable=True,
    )

    # --------------------------------
    # Source
    # --------------------------------

    source = Column(
        String(30),
        nullable=False,
        default="MANUAL",
    )

    # MANUAL
    # CAS_IMPORT
    # BROKER
    # RTA
    # ACCOUNT_AGGREGATOR

    source_reference = Column(
        String(255),
        nullable=True,
    )

    sync_status = Column(
        String(30),
        nullable=False,
        default="ACTIVE",
    )

    # ACTIVE
    # STALE
    # ERROR

    user = relationship(
        "User",
        back_populates="investment_holdings",
    )
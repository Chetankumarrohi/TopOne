from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.common.mixins import TimestampMixin
from app.core.database import Base


class PortfolioTransaction(Base, TimestampMixin):
    __tablename__ = "portfolio_transactions"

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

    holding_id = Column(
        Integer,
        ForeignKey(
            "investment_holdings.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # --------------------------------
    # Instrument Details
    # --------------------------------

    asset_type = Column(
        String(30),
        nullable=False,
    )
    # MUTUAL_FUND, STOCK, ETF, GOLD, BOND, PPF, EPF, NPS, CASH, OTHER

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

    # --------------------------------
    # Transaction Details
    # --------------------------------

    transaction_type = Column(
        String(30),
        nullable=False,
        index=True,
    )
    # BUY, SELL, SIP, REDEMPTION, DIVIDEND, BONUS, SPLIT, SWITCH_IN, SWITCH_OUT, FEE

    quantity = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    price = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    gross_amount = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    fees = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    taxes = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    net_amount = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    transaction_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    source = Column(
        String(30),
        nullable=False,
        default="MANUAL",
    )
    # MANUAL, CAS_IMPORT, BROKER, RTA, SYSTEM

    external_reference = Column(
        String(255),
        nullable=True,
        index=True,
    )

    notes = Column(
        String(500),
        nullable=True,
    )

    # --------------------------------
    # Relationships
    # --------------------------------

    user = relationship(
        "User",
        backref="portfolio_transactions",
    )

    holding = relationship(
        "InvestmentHolding",
        backref="transactions",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "external_reference",
            name="uq_user_external_ref",
        ),
    )

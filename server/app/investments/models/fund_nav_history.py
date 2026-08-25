from sqlalchemy import (
    Column,
    Integer,
    Float,
    Date,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from app.core.database import Base
from app.common.mixins import TimestampMixin


class FundNAVHistory(Base, TimestampMixin):
    __tablename__ = "fund_nav_history"

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

    nav_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    nav = Column(
        Float,
        nullable=False,
    )

    daily_change = Column(
        Float,
        nullable=True,
    )

    daily_change_percentage = Column(
        Float,
        nullable=True,
    )

    product = relationship(
        "InvestmentProduct",
    )

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "nav_date",
            name="uq_fund_nav_product_date",
        ),
    )
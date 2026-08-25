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


class InvestmentOrder(Base, TimestampMixin):
    __tablename__ = "investment_orders"

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

    product_id = Column(
        Integer,
        ForeignKey(
            "investment_products.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # -----------------------------
    # Order type
    # -----------------------------

    transaction_type = Column(
        String(30),
        nullable=False,
        default="PURCHASE",
    )

    # PURCHASE
    # REDEMPTION
    # SWITCH

    investment_mode = Column(
        String(30),
        nullable=False,
        default="LUMPSUM",
    )

    # LUMPSUM
    # SIP

    amount = Column(
        Float,
        nullable=False,
    )

    # -----------------------------
    # Order lifecycle
    # -----------------------------

    status = Column(
        String(30),
        nullable=False,
        default="PENDING",
    )

    # PENDING
    # KYC_REQUIRED
    # MANDATE_REQUIRED
    # PROCESSING
    # SUCCESS
    # FAILED
    # CANCELLED

    provider_order_id = Column(
        String(150),
        nullable=True,
        index=True,
    )

    failure_reason = Column(
        String(255),
        nullable=True,
    )

    execution_provider = Column(
        String(100),
        nullable=True,
    )

    user = relationship(
        "User",
    )

    product = relationship(
        "InvestmentProduct",
    )
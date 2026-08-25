from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    Text,
)

from app.core.database import Base
from app.common.mixins import TimestampMixin


class InvestmentProduct(Base, TimestampMixin):
    __tablename__ = "investment_products"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # =====================================================
    # BASIC IDENTITY
    # =====================================================

    name = Column(
        String(200),
        nullable=False,
    )

    product_type = Column(
        String(30),
        nullable=False,
        default="MUTUAL_FUND",
    )

    isin = Column(
        String(20),
        nullable=True,
        index=True,
    )

    symbol = Column(
        String(50),
        nullable=True,
        index=True,
    )

    scheme_code = Column(
        String(50),
        nullable=True,
        unique=True,
        index=True,
    )

    provider = Column(
        String(120),
        nullable=True,
    )

    # =====================================================
    # FUND CLASSIFICATION
    # =====================================================

    category = Column(
        String(100),
        nullable=True,
    )

    sub_category = Column(
        String(100),
        nullable=True,
    )

    asset_class = Column(
        String(50),
        nullable=True,
    )

    plan_type = Column(
        String(30),
        nullable=True,
    )

    option_type = Column(
        String(30),
        nullable=True,
    )

    risk_level = Column(
        String(50),
        nullable=True,
    )

    riskometer = Column(
        String(50),
        nullable=True,
    )

    # =====================================================
    # SCHEME LIFECYCLE
    # =====================================================

   
    scheme_status = Column(
        String(30),
        nullable=False,
        default="ACTIVE",
        index=True,
    )

    
    lifecycle_reason = Column(
        Text,
        nullable=True,
    )

    
    successor_scheme_code = Column(
        String(50),
        nullable=True,
        index=True,
    )

    
    last_seen_in_amfi = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    
    lifecycle_updated_at = Column(
        DateTime,
        nullable=True,
    )

    # =====================================================
    # NAV / PRICE
    # =====================================================

    nav = Column(
        Float,
        nullable=False,
        default=0,
    )

    nav_date = Column(
        Date,
        nullable=True,
    )

    previous_nav = Column(
        Float,
        nullable=True,
    )

    daily_change = Column(
        Float,
        nullable=True,
    )

    daily_change_percentage = Column(
        Float,
        nullable=True,
    )

    # =====================================================
    # FUND INFORMATION
    # =====================================================

    aum = Column(
        Float,
        nullable=True,
    )

    expense_ratio = Column(
        Float,
        nullable=False,
        default=0,
    )

    exit_load = Column(
        String(255),
        nullable=True,
    )

    benchmark = Column(
        String(150),
        nullable=True,
    )

    launch_date = Column(
        Date,
        nullable=True,
    )

    fund_manager = Column(
        String(200),
        nullable=True,
    )

    investment_objective = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # MINIMUM INVESTMENT
    # =====================================================

    minimum_sip = Column(
        Float,
        nullable=False,
        default=0,
    )

    minimum_lumpsum = Column(
        Float,
        nullable=False,
        default=0,
    )

    # =====================================================
    # RETURNS
    # =====================================================

    return_1d = Column(
        Float,
        nullable=True,
    )

    return_1m = Column(
        Float,
        nullable=True,
    )

    return_3m = Column(
        Float,
        nullable=True,
    )

    return_6m = Column(
        Float,
        nullable=True,
    )

    return_1y = Column(
        Float,
        nullable=False,
        default=0,
    )

    return_3y = Column(
        Float,
        nullable=False,
        default=0,
    )

    return_5y = Column(
        Float,
        nullable=False,
        default=0,
    )

    # =====================================================
    # RISK / PERFORMANCE METRICS
    # =====================================================

    volatility = Column(
        Float,
        nullable=False,
        default=0,
    )

    alpha = Column(
        Float,
        nullable=True,
    )

    beta = Column(
        Float,
        nullable=True,
    )

    sharpe_ratio = Column(
        Float,
        nullable=True,
    )

    standard_deviation = Column(
        Float,
        nullable=True,
    )

    portfolio_turnover = Column(
        Float,
        nullable=True,
    )

    # =====================================================
    # PORTFOLIO INFORMATION
    # =====================================================

    equity_percentage = Column(
        Float,
        nullable=True,
    )

    debt_percentage = Column(
        Float,
        nullable=True,
    )

    cash_percentage = Column(
        Float,
        nullable=True,
    )

    large_cap_percentage = Column(
        Float,
        nullable=True,
    )

    mid_cap_percentage = Column(
        Float,
        nullable=True,
    )

    small_cap_percentage = Column(
        Float,
        nullable=True,
    )

    holdings_as_of = Column(
        Date,
        nullable=True,
    )

    # =====================================================
    # FUND HEALTH INTELLIGENCE
    # =====================================================

    # Overall score from 0 to 100.
    fund_health_score = Column(
        Float,
        nullable=True,
    )

    # -----------------------------------------------------
    # Individual health components
    # -----------------------------------------------------

    consistency_score = Column(
        Float,
        nullable=True,
    )

    rolling_return_score = Column(
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

    long_term_score = Column(
        Float,
        nullable=True,
    )

    data_quality_score = Column(
        Float,
        nullable=True,
    )

    # -----------------------------------------------------
    # Relative performance
    # -----------------------------------------------------

    # Position of the fund compared with funds
    # in the same category/sub-category.
    peer_percentile = Column(
        Float,
        nullable=True,
    )

    # -----------------------------------------------------
    # Final classification
    # -----------------------------------------------------

    # Possible values:
    #
    # IN_FORM
    # ON_TRACK
    # OFF_TRACK
    # NOT_IN_FORM
    # UNRATED
    #
    fund_status = Column(
        String(30),
        nullable=True,
        index=True,
    )

    # Explanation generated by the health engine.
    fund_health_summary = Column(
        Text,
        nullable=True,
    )

    # When the health score was last calculated.
    health_calculated_at = Column(
        DateTime,
        nullable=True,
    )

    # =====================================================
    # PRODUCT AVAILABILITY
    # =====================================================

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    purchase_allowed = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    sip_allowed = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    # =====================================================
    # DATA SOURCE
    # =====================================================

    source = Column(
        String(50),
        nullable=False,
        default="DEMO",
    )

    data_updated_at = Column(
        DateTime,
        nullable=True,
    )
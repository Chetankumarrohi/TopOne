from datetime import datetime, date

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class InvestmentProductResponse(BaseModel):
    id: int

    name: str
    product_type: str

    isin: str | None
    symbol: str | None
    scheme_code: str | None
    provider: str | None

    category: str | None
    sub_category: str | None
    asset_class: str | None

    plan_type: str | None
    option_type: str | None

    risk_level: str | None
    riskometer: str | None

    # -----------------------------------------------------
    # NAV / PRICE
    # -----------------------------------------------------

    nav: float
    nav_date: date | None

    previous_nav: float | None
    daily_change: float | None
    daily_change_percentage: float | None

    # -----------------------------------------------------
    # FUND INFORMATION
    # -----------------------------------------------------

    aum: float | None
    expense_ratio: float

    exit_load: str | None
    benchmark: str | None
    launch_date: date | None
    fund_manager: str | None
    investment_objective: str | None

    # -----------------------------------------------------
    # MINIMUM INVESTMENT
    # -----------------------------------------------------

    minimum_sip: float
    minimum_lumpsum: float

    # -----------------------------------------------------
    # RETURNS
    # -----------------------------------------------------

    return_1d: float | None
    return_1m: float | None
    return_3m: float | None
    return_6m: float | None

    return_1y: float
    return_3y: float
    return_5y: float

    # -----------------------------------------------------
    # RISK / PERFORMANCE METRICS
    # -----------------------------------------------------

    volatility: float

    alpha: float | None
    beta: float | None
    sharpe_ratio: float | None
    standard_deviation: float | None
    portfolio_turnover: float | None

    # -----------------------------------------------------
    # PORTFOLIO INFORMATION
    # -----------------------------------------------------

    equity_percentage: float | None
    debt_percentage: float | None
    cash_percentage: float | None

    large_cap_percentage: float | None
    mid_cap_percentage: float | None
    small_cap_percentage: float | None

    holdings_as_of: date | None

    # -----------------------------------------------------
    # FUND HEALTH INTELLIGENCE
    # -----------------------------------------------------

    fund_health_score: float | None

    consistency_score: float | None
    rolling_return_score: float | None
    risk_adjusted_score: float | None
    downside_score: float | None
    volatility_score: float | None
    momentum_score: float | None
    long_term_score: float | None

    data_quality_score: float | None
    peer_percentile: float | None

    fund_status: str | None
    fund_health_summary: str | None
    health_calculated_at: datetime | None

    # -----------------------------------------------------
    # AVAILABILITY / SOURCE
    # -----------------------------------------------------

    purchase_allowed: bool
    sip_allowed: bool

    source: str
    data_updated_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )


class InvestmentOrderCreate(BaseModel):
    product_id: int

    investment_mode: str = Field(
        default="LUMPSUM",
    )

    amount: float = Field(
        ...,
        gt=0,
    )


class InvestmentOrderResponse(BaseModel):
    id: int

    user_id: int
    product_id: int

    transaction_type: str
    investment_mode: str

    amount: float
    status: str

    provider_order_id: str | None
    failure_reason: str | None

    execution_provider: str | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

   
# =====================================================
# PEER COMPARISON
# =====================================================

class PeerMetricComparison(BaseModel):
    fund: float | None
    peer_median: float | None
    difference: float | None

    # BETTER / WORSE / IN_LINE / UNAVAILABLE
    comparison: str


class PeerComparisonMetrics(BaseModel):
    return_1y: PeerMetricComparison
    return_3y: PeerMetricComparison
    return_5y: PeerMetricComparison

    volatility: PeerMetricComparison
    expense_ratio: PeerMetricComparison
    sharpe_ratio: PeerMetricComparison


class FundPeerComparisonResponse(BaseModel):
    product_id: int

    peer_group: str
    category_label: str

    category_rank: int | None
    category_size: int

    fund_status: str

    metrics: PeerComparisonMetrics

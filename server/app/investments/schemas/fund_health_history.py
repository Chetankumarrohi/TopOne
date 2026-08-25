from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class FundHealthHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int

    snapshot_date: date
    calculated_at: datetime

    fund_health_score: float | None
    fund_status: str

    history_days: int
    data_quality_score: float | None

    long_term_score: float | None
    consistency_score: float | None
    risk_adjusted_score: float | None
    downside_score: float | None
    volatility_score: float | None
    momentum_score: float | None
    peer_percentile: float | None
    quality_score: float | None
    fundamental_score: float | None
    news_score: float | None

    fund_health_summary: str | None
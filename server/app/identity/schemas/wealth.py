from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WealthDNAResponse(BaseModel):
    id: int
    user_id: int

    wealth_score: float
    investor_personality: str

    financial_stability_score: float
    savings_discipline_score: float
    debt_health_score: float
    emergency_preparedness_score: float
    investment_readiness_score: float
    goal_readiness_score: float
    risk_alignment_score: float

    strongest_trait: str | None
    improvement_area: str | None

    scoring_version: str

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
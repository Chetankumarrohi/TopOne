from pydantic import BaseModel


class FinancialTwinResponse(BaseModel):
    # Core position
    net_worth: float
    monthly_income: float
    monthly_expenses: float
    monthly_surplus: float

    # Financial health
    savings_rate: float
    emergency_months: float
    debt_to_income_ratio: float
    investment_ratio: float

    # Risk + Wealth DNA
    risk_score: float
    risk_category: str

    wealth_score: float
    investor_personality: str

    # Goals
    active_goals: int
    total_goal_target: float
    total_goal_saved: float
    goal_progress_percentage: float

    # Forward-looking twin
    projected_net_worth_1y: float
    projected_net_worth_3y: float
    projected_net_worth_5y: float
    projected_net_worth_10y: float

    # Resilience
    financial_runway_months: float
    financial_health_score: float

    # Interpretation
    financial_status: str
    next_priority: str
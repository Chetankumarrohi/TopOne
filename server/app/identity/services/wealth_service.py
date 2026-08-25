from sqlalchemy.orm import Session

from app.identity.models.wealth_dna import WealthDNA
from app.identity.models.financial_profile import FinancialProfile
from app.identity.models.risk_profile import RiskProfile
from app.identity.models.investment_goal import InvestmentGoal


WEALTH_SCORING_VERSION = "wealth-v1.0"


def clamp(value: float) -> float:
    return max(
        0.0,
        min(round(value, 2), 100.0),
    )


def calculate_financial_stability(
    financial: FinancialProfile,
) -> float:
    score = 0.0

    if financial.net_worth > 0:
        score += 30

    if financial.savings_rate >= 30:
        score += 30
    elif financial.savings_rate >= 20:
        score += 24
    elif financial.savings_rate >= 10:
        score += 15
    elif financial.savings_rate > 0:
        score += 8

    if financial.emergency_months >= 6:
        score += 25
    elif financial.emergency_months >= 3:
        score += 18
    elif financial.emergency_months >= 1:
        score += 10

    if financial.total_liabilities <= 0:
        score += 15
    elif financial.debt_to_income_ratio <= 20:
        score += 12
    elif financial.debt_to_income_ratio <= 40:
        score += 6

    return clamp(score)


def calculate_savings_discipline(
    financial: FinancialProfile,
) -> float:
    rate = financial.savings_rate

    if rate >= 40:
        return 100

    if rate >= 30:
        return 90

    if rate >= 20:
        return 75

    if rate >= 10:
        return 55

    if rate > 0:
        return 30

    return 0


def calculate_debt_health(
    financial: FinancialProfile,
) -> float:
    ratio = financial.debt_to_income_ratio

    if financial.total_liabilities <= 0:
        return 100

    if ratio <= 10:
        return 95

    if ratio <= 20:
        return 80

    if ratio <= 30:
        return 65

    if ratio <= 40:
        return 45

    if ratio <= 50:
        return 25

    return 10


def calculate_emergency_preparedness(
    financial: FinancialProfile,
) -> float:
    months = financial.emergency_months

    if months >= 9:
        return 100

    if months >= 6:
        return 90

    if months >= 3:
        return 70

    if months >= 1:
        return 40

    if months > 0:
        return 20

    return 0


def calculate_investment_readiness(
    financial: FinancialProfile,
) -> float:
    score = 0.0

    if financial.existing_investments > 0:
        score += 35

    if financial.investment_ratio >= 30:
        score += 35
    elif financial.investment_ratio >= 20:
        score += 30
    elif financial.investment_ratio >= 10:
        score += 20
    elif financial.investment_ratio > 0:
        score += 10

    if financial.savings_rate >= 20:
        score += 20
    elif financial.savings_rate >= 10:
        score += 10

    if financial.emergency_months >= 3:
        score += 10

    return clamp(score)


def calculate_goal_readiness(
    goals: list[InvestmentGoal],
) -> float:
    if not goals:
        return 0

    scores = []

    for goal in goals:
        score = goal.progress_percentage

        if (
            goal.monthly_contribution
            >= goal.required_monthly_investment
            and goal.required_monthly_investment > 0
        ):
            score += 25

        if goal.priority <= 2:
            score += 10

        scores.append(
            clamp(score)
        )

    return clamp(
        sum(scores) / len(scores)
    )


def calculate_risk_alignment(
    risk: RiskProfile,
) -> float:
    capacity = risk.capacity_score
    behaviour = risk.behaviour_score

    difference = abs(
        capacity - behaviour
    )

    alignment = 100 - difference

    return clamp(alignment)


def determine_personality(
    savings_score: float,
    debt_score: float,
    investment_score: float,
    risk: RiskProfile,
) -> str:
    if (
        savings_score >= 75
        and debt_score >= 75
        and risk.final_risk_score >= 70
    ):
        return "Growth Builder"

    if (
        savings_score >= 70
        and risk.final_risk_score < 40
    ):
        return "Disciplined Protector"

    if (
        investment_score >= 70
        and risk.final_risk_score >= 60
    ):
        return "Confident Investor"

    if (
        debt_score < 40
        or savings_score < 40
    ):
        return "Financial Rebuilder"

    return "Balanced Wealth Builder"


def find_trait(
    scores: dict[str, float],
):
    labels = {
        "financial_stability": "Financial Stability",
        "savings_discipline": "Savings Discipline",
        "debt_health": "Debt Health",
        "emergency_preparedness":
            "Emergency Preparedness",
        "investment_readiness":
            "Investment Readiness",
        "goal_readiness": "Goal Readiness",
        "risk_alignment": "Risk Alignment",
    }

    strongest_key = max(
        scores,
        key=scores.get,
    )

    weakest_key = min(
        scores,
        key=scores.get,
    )

    return (
        labels[strongest_key],
        labels[weakest_key],
    )


def generate_wealth_dna(
    db: Session,
    user_id: int,
):
    financial = (
        db.query(FinancialProfile)
        .filter(
            FinancialProfile.user_id == user_id
        )
        .first()
    )

    if not financial:
        raise ValueError(
            "Complete your financial profile first."
        )

    risk = (
        db.query(RiskProfile)
        .filter(
            RiskProfile.user_id == user_id
        )
        .first()
    )

    if not risk:
        raise ValueError(
            "Complete your risk assessment first."
        )

    goals = (
        db.query(InvestmentGoal)
        .filter(
            InvestmentGoal.user_id == user_id,
            InvestmentGoal.status == "ACTIVE",
        )
        .all()
    )

    financial_stability = (
        calculate_financial_stability(
            financial
        )
    )

    savings_discipline = (
        calculate_savings_discipline(
            financial
        )
    )

    debt_health = (
        calculate_debt_health(
            financial
        )
    )

    emergency_preparedness = (
        calculate_emergency_preparedness(
            financial
        )
    )

    investment_readiness = (
        calculate_investment_readiness(
            financial
        )
    )

    goal_readiness = (
        calculate_goal_readiness(
            goals
        )
    )

    risk_alignment = (
        calculate_risk_alignment(
            risk
        )
    )

    scores = {
        "financial_stability":
            financial_stability,

        "savings_discipline":
            savings_discipline,

        "debt_health":
            debt_health,

        "emergency_preparedness":
            emergency_preparedness,

        "investment_readiness":
            investment_readiness,

        "goal_readiness":
            goal_readiness,

        "risk_alignment":
            risk_alignment,
    }

    wealth_score = clamp(
        financial_stability * 0.20
        + savings_discipline * 0.15
        + debt_health * 0.15
        + emergency_preparedness * 0.15
        + investment_readiness * 0.15
        + goal_readiness * 0.10
        + risk_alignment * 0.10
    )

    personality = determine_personality(
        savings_score=savings_discipline,
        debt_score=debt_health,
        investment_score=investment_readiness,
        risk=risk,
    )

    strongest_trait, improvement_area = (
        find_trait(scores)
    )

    wealth_dna = (
        db.query(WealthDNA)
        .filter(
            WealthDNA.user_id == user_id
        )
        .first()
    )

    if not wealth_dna:
        wealth_dna = WealthDNA(
            user_id=user_id
        )

        db.add(wealth_dna)

    wealth_dna.wealth_score = wealth_score

    wealth_dna.investor_personality = (
        personality
    )

    wealth_dna.financial_stability_score = (
        financial_stability
    )

    wealth_dna.savings_discipline_score = (
        savings_discipline
    )

    wealth_dna.debt_health_score = (
        debt_health
    )

    wealth_dna.emergency_preparedness_score = (
        emergency_preparedness
    )

    wealth_dna.investment_readiness_score = (
        investment_readiness
    )

    wealth_dna.goal_readiness_score = (
        goal_readiness
    )

    wealth_dna.risk_alignment_score = (
        risk_alignment
    )

    wealth_dna.strongest_trait = (
        strongest_trait
    )

    wealth_dna.improvement_area = (
        improvement_area
    )

    wealth_dna.scoring_version = (
        WEALTH_SCORING_VERSION
    )

    db.commit()
    db.refresh(wealth_dna)

    return wealth_dna


def get_wealth_dna(
    db: Session,
    user_id: int,
):
    wealth_dna = (
        db.query(WealthDNA)
        .filter(
            WealthDNA.user_id == user_id
        )
        .first()
    )

    if not wealth_dna:
        raise ValueError(
            "Wealth DNA has not been generated yet."
        )

    return wealth_dna
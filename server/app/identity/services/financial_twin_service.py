from sqlalchemy.orm import Session

from app.identity.models.financial_profile import FinancialProfile
from app.identity.models.risk_profile import RiskProfile
from app.identity.models.investment_goal import InvestmentGoal
from app.identity.models.wealth_dna import WealthDNA


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    return max(
        minimum,
        min(round(value, 2), maximum),
    )


def calculate_future_value(
    current_net_worth: float,
    monthly_surplus: float,
    annual_return: float,
    years: int,
) -> float:
    """
    Simple deterministic wealth projection.

    Current wealth compounds annually.
    Monthly surplus is invested monthly.
    """

    annual_return_decimal = (
        annual_return / 100
    )

    monthly_return = (
        annual_return_decimal / 12
    )

    months = years * 12

    future_existing_wealth = (
        current_net_worth
        * (
            (1 + annual_return_decimal)
            ** years
        )
    )

    if monthly_return > 0:
        future_contributions = (
            monthly_surplus
            * (
                (
                    (1 + monthly_return)
                    ** months
                )
                - 1
            )
            / monthly_return
        )
    else:
        future_contributions = (
            monthly_surplus * months
        )

    return round(
        max(
            future_existing_wealth
            + future_contributions,
            0,
        ),
        2,
    )


def expected_return_from_risk(
    risk: RiskProfile,
) -> float:
    """
    Conservative assumptions for simulation only.
    These are not investment guarantees.
    """

    category = (
        risk.risk_category
        or ""
    ).lower()

    if category == "conservative":
        return 6.0

    if category == "moderate":
        return 9.0

    if category == "aggressive":
        return 12.0

    return 8.0


def calculate_goal_summary(
    goals: list[InvestmentGoal],
):
    active_goals = [
        goal
        for goal in goals
        if goal.status == "ACTIVE"
    ]

    total_target = sum(
        goal.target_amount
        for goal in active_goals
    )

    total_saved = sum(
        goal.current_amount
        for goal in active_goals
    )

    if total_target > 0:
        progress = (
            total_saved
            / total_target
        ) * 100
    else:
        progress = 0

    return {
        "active_goals": len(
            active_goals
        ),
        "total_target": round(
            total_target,
            2,
        ),
        "total_saved": round(
            total_saved,
            2,
        ),
        "progress": clamp(
            progress
        ),
    }


def calculate_health_score(
    financial: FinancialProfile,
    risk: RiskProfile,
    wealth: WealthDNA,
    goal_progress: float,
) -> float:
    """
    Overall Financial Twin health score.
    """

    savings_component = clamp(
        (
            financial.savings_rate
            / 30
        )
        * 100
    )

    emergency_component = clamp(
        (
            financial.emergency_months
            / 6
        )
        * 100
    )

    debt_component = clamp(
        100
        - financial.debt_to_income_ratio
    )

    net_worth_component = (
        100
        if financial.net_worth > 0
        else 20
    )

    score = (
        savings_component * 0.20
        + emergency_component * 0.20
        + debt_component * 0.15
        + net_worth_component * 0.10
        + wealth.wealth_score * 0.20
        + risk.final_risk_score * 0.05
        + goal_progress * 0.10
    )

    return clamp(score)


def determine_financial_status(
    score: float,
) -> str:
    if score >= 85:
        return "Excellent"

    if score >= 70:
        return "Strong"

    if score >= 55:
        return "Stable"

    if score >= 40:
        return "Developing"

    return "Needs Attention"


def determine_next_priority(
    financial: FinancialProfile,
    goals: list[InvestmentGoal],
) -> str:
    if financial.emergency_months < 3:
        return (
            "Build your emergency fund "
            "to at least 3 months of expenses."
        )

    if (
        financial.debt_to_income_ratio
        > 40
    ):
        return (
            "Reduce high debt exposure "
            "before increasing investment risk."
        )

    if financial.savings_rate < 20:
        return (
            "Increase your monthly savings "
            "rate toward 20%."
        )

    active_goals = [
        goal
        for goal in goals
        if goal.status == "ACTIVE"
    ]

    underfunded_goals = [
        goal
        for goal in active_goals
        if (
            goal.required_monthly_investment
            > goal.monthly_contribution
        )
    ]

    if underfunded_goals:
        highest_priority = sorted(
            underfunded_goals,
            key=lambda goal: goal.priority,
        )[0]

        return (
            f"Increase contributions toward "
            f"'{highest_priority.goal_name}'."
        )

    if (
        financial.existing_investments
        <= 0
    ):
        return (
            "Begin building a diversified "
            "investment portfolio."
        )

    return (
        "Maintain your current financial "
        "discipline and review your goals regularly."
    )


def get_financial_twin(
    db: Session,
    user_id: int,
):
    # --------------------------------
    # Financial Profile
    # --------------------------------

    financial = (
        db.query(FinancialProfile)
        .filter(
            FinancialProfile.user_id
            == user_id
        )
        .first()
    )

    if not financial:
        raise ValueError(
            "Complete your financial profile first."
        )

    # --------------------------------
    # Risk Profile
    # --------------------------------

    risk = (
        db.query(RiskProfile)
        .filter(
            RiskProfile.user_id
            == user_id
        )
        .first()
    )

    if not risk:
        raise ValueError(
            "Complete your risk assessment first."
        )

    # --------------------------------
    # Wealth DNA
    # --------------------------------

    wealth = (
        db.query(WealthDNA)
        .filter(
            WealthDNA.user_id
            == user_id
        )
        .first()
    )

    if not wealth:
        raise ValueError(
            "Generate your Wealth DNA first."
        )

    # --------------------------------
    # Goals
    # --------------------------------

    goals = (
        db.query(InvestmentGoal)
        .filter(
            InvestmentGoal.user_id
            == user_id
        )
        .all()
    )

    # --------------------------------
    # Core calculations
    # --------------------------------

    monthly_surplus = max(
        financial.monthly_income
        - financial.monthly_expenses
        - financial.monthly_debt_payment,
        0,
    )

    annual_return = (
        expected_return_from_risk(
            risk
        )
    )

    goal_summary = (
        calculate_goal_summary(
            goals
        )
    )

    health_score = (
        calculate_health_score(
            financial=financial,
            risk=risk,
            wealth=wealth,
            goal_progress=goal_summary[
                "progress"
            ],
        )
    )

    # --------------------------------
    # Projection
    # --------------------------------

    projected_1y = (
        calculate_future_value(
            financial.net_worth,
            monthly_surplus,
            annual_return,
            1,
        )
    )

    projected_3y = (
        calculate_future_value(
            financial.net_worth,
            monthly_surplus,
            annual_return,
            3,
        )
    )

    projected_5y = (
        calculate_future_value(
            financial.net_worth,
            monthly_surplus,
            annual_return,
            5,
        )
    )

    projected_10y = (
        calculate_future_value(
            financial.net_worth,
            monthly_surplus,
            annual_return,
            10,
        )
    )

    return {
        "net_worth":
            financial.net_worth,

        "monthly_income":
            financial.monthly_income,

        "monthly_expenses":
            financial.monthly_expenses,

        "monthly_surplus":
            round(
                monthly_surplus,
                2,
            ),

        "savings_rate":
            financial.savings_rate,

        "emergency_months":
            financial.emergency_months,

        "debt_to_income_ratio":
            financial.debt_to_income_ratio,

        "investment_ratio":
            financial.investment_ratio,

        "risk_score":
            risk.final_risk_score,

        "risk_category":
            risk.risk_category,

        "wealth_score":
            wealth.wealth_score,

        "investor_personality":
            wealth.investor_personality,

        "active_goals":
            goal_summary[
                "active_goals"
            ],

        "total_goal_target":
            goal_summary[
                "total_target"
            ],

        "total_goal_saved":
            goal_summary[
                "total_saved"
            ],

        "goal_progress_percentage":
            goal_summary[
                "progress"
            ],

        "projected_net_worth_1y":
            projected_1y,

        "projected_net_worth_3y":
            projected_3y,

        "projected_net_worth_5y":
            projected_5y,

        "projected_net_worth_10y":
            projected_10y,

        "financial_runway_months":
            round(
                financial.emergency_months,
                2,
            ),

        "financial_health_score":
            health_score,

        "financial_status":
            determine_financial_status(
                health_score
            ),

        "next_priority":
            determine_next_priority(
                financial,
                goals,
            ),
    }
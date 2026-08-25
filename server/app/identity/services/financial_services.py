from sqlalchemy.orm import Session

from app.identity.models.financial_profile import FinancialProfile

from app.identity.repositories.financial_repository import (
    get_by_user,
    create,
    update,
)


def calculate_financial_metrics(
    profile: FinancialProfile,
) -> FinancialProfile:

    # 1. Net Worth
    profile.net_worth = (
        profile.total_assets
        - profile.total_liabilities
    )

    # 2. Savings Rate
    if profile.monthly_income > 0:
        monthly_savings = (
            profile.monthly_income
            - profile.monthly_expenses
        )

        profile.savings_rate = (
            monthly_savings
            / profile.monthly_income
        ) * 100
    else:
        profile.savings_rate = 0

    # 3. Debt-to-Income Ratio
    if profile.monthly_income > 0:
        profile.debt_to_income_ratio = (
            profile.monthly_debt_payment
            / profile.monthly_income
        ) * 100
    else:
        profile.debt_to_income_ratio = 0

    # 4. Emergency Fund Coverage
    if profile.monthly_expenses > 0:
        profile.emergency_months = (
            profile.emergency_fund
            / profile.monthly_expenses
        )
    else:
        profile.emergency_months = 0

    # 5. Investment Ratio
    if profile.total_assets > 0:
        profile.investment_ratio = (
            profile.existing_investments
            / profile.total_assets
        ) * 100
    else:
        profile.investment_ratio = 0

    return profile


def create_financial_profile(
    db: Session,
    user_id: int,
    data,
):
    existing_profile = get_by_user(
        db,
        user_id,
    )

    if existing_profile:
        raise ValueError(
            "Financial profile already exists."
        )

    profile = FinancialProfile(
        user_id=user_id,
        annual_income=data.annual_income,
        monthly_income=data.monthly_income,
        monthly_expenses=data.monthly_expenses,
        monthly_debt_payment=data.monthly_debt_payment,
        total_savings=data.total_savings,
        emergency_fund=data.emergency_fund,
        total_assets=data.total_assets,
        total_liabilities=data.total_liabilities,
        existing_investments=data.existing_investments,
        insurance_cover=data.insurance_cover,
    )

    calculate_financial_metrics(profile)

    return create(
        db,
        profile,
    )


def get_financial_profile(
    db: Session,
    user_id: int,
):
    profile = get_by_user(
        db,
        user_id,
    )

    if not profile:
        raise ValueError(
            "Financial profile not found."
        )

    return profile


def update_financial_profile(
    db: Session,
    user_id: int,
    data,
):
    profile = get_by_user(
        db,
        user_id,
    )

    if not profile:
        raise ValueError(
            "Financial profile not found."
        )

    updated_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in updated_data.items():
        setattr(
            profile,
            field,
            value,
        )

    calculate_financial_metrics(profile)

    return update(
        db,
        profile,
    )
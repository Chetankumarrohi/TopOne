from datetime import date

from sqlalchemy.orm import Session

from app.identity.models.investment_goal import InvestmentGoal

from app.identity.repositories.goal_repository import (
    get_all_by_user,
    get_by_id,
    create,
    update,
    delete,
)


def calculate_months_remaining(
    target_date: date,
) -> int:
    today = date.today()

    if target_date <= today:
        return 0

    months = (
        (target_date.year - today.year) * 12
        + (target_date.month - today.month)
    )

    if target_date.day < today.day:
        months -= 1

    return max(months, 0)


def calculate_goal_metrics(
    goal: InvestmentGoal,
) -> InvestmentGoal:

    # --------------------------------
    # Progress Percentage
    # --------------------------------

    if goal.target_amount > 0:
        goal.progress_percentage = min(
            round(
                (
                    goal.current_amount
                    / goal.target_amount
                )
                * 100,
                2,
            ),
            100.0,
        )
    else:
        goal.progress_percentage = 0

    # --------------------------------
    # Months Remaining
    # --------------------------------

    goal.months_remaining = (
        calculate_months_remaining(
            goal.target_date
        )
    )

    # --------------------------------
    # Remaining Amount
    # --------------------------------

    remaining_amount = max(
        goal.target_amount
        - goal.current_amount,
        0,
    )

    # --------------------------------
    # Required Monthly Investment
    # --------------------------------

    if goal.months_remaining > 0:
        goal.required_monthly_investment = round(
            remaining_amount
            / goal.months_remaining,
            2,
        )
    else:
        goal.required_monthly_investment = (
            remaining_amount
        )

    # --------------------------------
    # Status
    # --------------------------------

    if (
        goal.current_amount
        >= goal.target_amount
    ):
        goal.status = "COMPLETED"

    return goal


def create_goal(
    db: Session,
    user_id: int,
    data,
):
    if data.target_date <= date.today():
        raise ValueError(
            "Target date must be in the future."
        )

    if data.current_amount > data.target_amount:
        raise ValueError(
            "Current amount cannot be greater than target amount."
        )

    goal = InvestmentGoal(
        user_id=user_id,
        goal_name=data.goal_name,
        goal_type=data.goal_type.upper(),
        target_amount=data.target_amount,
        current_amount=data.current_amount,
        target_date=data.target_date,
        monthly_contribution=data.monthly_contribution,
        priority=data.priority,
        status="ACTIVE",
    )

    calculate_goal_metrics(goal)

    return create(
        db,
        goal,
    )


def get_goals(
    db: Session,
    user_id: int,
):
    goals = get_all_by_user(
        db,
        user_id,
    )

    return goals


def get_goal(
    db: Session,
    user_id: int,
    goal_id: int,
):
    goal = get_by_id(
        db,
        goal_id,
        user_id,
    )

    if not goal:
        raise ValueError(
            "Goal not found."
        )

    return goal


def update_goal(
    db: Session,
    user_id: int,
    goal_id: int,
    data,
):
    goal = get_by_id(
        db,
        goal_id,
        user_id,
    )

    if not goal:
        raise ValueError(
            "Goal not found."
        )

    updates = data.model_dump(
        exclude_unset=True
    )

    for field, value in updates.items():
        if (
            field == "goal_type"
            and value is not None
        ):
            value = value.upper()

        setattr(
            goal,
            field,
            value,
        )

    if goal.target_date <= date.today():
        raise ValueError(
            "Target date must be in the future."
        )

    if goal.current_amount > goal.target_amount:
        raise ValueError(
            "Current amount cannot be greater than target amount."
        )

    calculate_goal_metrics(goal)

    return update(
        db,
        goal,
    )


def delete_goal(
    db: Session,
    user_id: int,
    goal_id: int,
):
    goal = get_by_id(
        db,
        goal_id,
        user_id,
    )

    if not goal:
        raise ValueError(
            "Goal not found."
        )

    delete(
        db,
        goal,
    )

    return {
        "message": "Goal deleted successfully."
    }
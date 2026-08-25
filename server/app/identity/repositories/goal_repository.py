from sqlalchemy.orm import Session

from app.identity.models.investment_goal import InvestmentGoal


def get_all_by_user(
    db: Session,
    user_id: int,
):
    return (
        db.query(InvestmentGoal)
        .filter(
            InvestmentGoal.user_id == user_id
        )
        .order_by(
            InvestmentGoal.priority.asc(),
            InvestmentGoal.target_date.asc(),
        )
        .all()
    )


def get_by_id(
    db: Session,
    goal_id: int,
    user_id: int,
):
    return (
        db.query(InvestmentGoal)
        .filter(
            InvestmentGoal.id == goal_id,
            InvestmentGoal.user_id == user_id,
        )
        .first()
    )


def create(
    db: Session,
    goal: InvestmentGoal,
):
    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal


def update(
    db: Session,
    goal: InvestmentGoal,
):
    db.commit()
    db.refresh(goal)

    return goal


def delete(
    db: Session,
    goal: InvestmentGoal,
):
    db.delete(goal)
    db.commit()
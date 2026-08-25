from sqlalchemy.orm import Session

from app.identity.models.financial_profile import FinancialProfile


def get_by_user(
    db: Session,
    user_id: int,
):
    return (
        db.query(FinancialProfile)
        .filter(FinancialProfile.user_id == user_id)
        .first()
    )


def create(
    db: Session,
    profile: FinancialProfile,
):
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


def update(
    db: Session,
    profile: FinancialProfile,
):
    db.commit()
    db.refresh(profile)

    return profile
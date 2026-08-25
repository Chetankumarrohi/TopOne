from sqlalchemy.orm import Session

from app.identity.models.risk_profile import RiskProfile


def get_by_user(
    db: Session,
    user_id: int,
):
    return (
        db.query(RiskProfile)
        .filter(
            RiskProfile.user_id == user_id
        )
        .first()
    )


def create(
    db: Session,
    profile: RiskProfile,
):
    db.add(profile)

    db.commit()

    db.refresh(profile)

    return profile


def update(
    db: Session,
    profile: RiskProfile,
):
    db.commit()

    db.refresh(profile)

    return profile
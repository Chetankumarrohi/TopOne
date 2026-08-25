from sqlalchemy.orm import Session

from app.identity.models.user_profile import UserProfile


def get_profile(db: Session, user_id: int):
    return (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )


def create_profile(db: Session, profile: UserProfile):
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
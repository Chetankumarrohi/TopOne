from sqlalchemy.orm import Session

from app.identity.models.user_profile import UserProfile
from app.identity.repositories.profile_repository import (
    create_profile,
    get_profile,
)


def create_user_profile(db, current_user, data):

    existing = get_profile(db, current_user.id)

    if existing:
        raise ValueError("Profile already exists.")

    profile = UserProfile(
        user_id=current_user.id,
        phone=data.phone,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        occupation=data.occupation,
        marital_status=data.marital_status,
        country=data.country,
        state=data.state,
        city=data.city,
    )

    return create_profile(db, profile)


def get_user_profile(db: Session, current_user):
    profile = get_profile(db, current_user.id)

    if profile is None:
        raise ValueError("Profile not found.")

    return profile
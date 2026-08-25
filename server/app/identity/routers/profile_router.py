from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db

from app.identity.schemas.profile import (
    ProfileCreate,
    ProfileResponse,
)

from app.identity.services.profile_service import (
    create_user_profile,
    get_user_profile,
)

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


@router.post("", response_model=ProfileResponse)
def create_profile(
    profile: ProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return create_user_profile(
            db,
            current_user,
            profile,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return get_user_profile(
            db,
            current_user,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
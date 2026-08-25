from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user

from app.identity.schemas.risk import (
    RiskAssessmentCreate,
    RiskAssessmentUpdate,
    RiskProfileResponse,
    RiskQuestionResponse,
)

from app.identity.services.risk_service import (
    create_risk_profile,
    get_risk_profile,
    update_risk_profile,
    get_risk_questions,
)


router = APIRouter(
    prefix="/risk",
    tags=["Risk Assessment"],
)


@router.get(
    "/questions",
    response_model=list[RiskQuestionResponse],
)
def questions():
    return get_risk_questions()


@router.post(
    "/assessment",
    response_model=RiskProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment(
    data: RiskAssessmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return create_risk_profile(
            db=db,
            user_id=current_user.id,
            data=data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.get(
    "/profile",
    response_model=RiskProfileResponse,
)
def get_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return get_risk_profile(
            db=db,
            user_id=current_user.id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.put(
    "/assessment",
    response_model=RiskProfileResponse,
)
def reassess(
    data: RiskAssessmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return update_risk_profile(
            db=db,
            user_id=current_user.id,
            data=data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
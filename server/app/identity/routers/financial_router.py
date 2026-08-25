from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user

from app.identity.schemas.financial import (
    FinancialProfileCreate,
    FinancialProfileUpdate,
    FinancialProfileResponse,
)

from app.identity.services.financial_services import (
    create_financial_profile,
    get_financial_profile,
    update_financial_profile,
)


router = APIRouter(
    prefix="/financial-profile",
    tags=["Financial Profile"],
)


@router.post(
    "",
    response_model=FinancialProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    data: FinancialProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return create_financial_profile(
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
    "",
    response_model=FinancialProfileResponse,
    status_code=status.HTTP_200_OK,
)
def get_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return get_financial_profile(
            db=db,
            user_id=current_user.id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.put(
    "",
    response_model=FinancialProfileResponse,
    status_code=status.HTTP_200_OK,
)
def update_profile(
    data: FinancialProfileUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return update_financial_profile(
            db=db,
            user_id=current_user.id,
            data=data,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
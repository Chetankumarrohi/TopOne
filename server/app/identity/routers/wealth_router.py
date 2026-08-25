from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user

from app.identity.schemas.wealth import (
    WealthDNAResponse,
)

from app.identity.services.wealth_service import (
    generate_wealth_dna,
    get_wealth_dna,
)


router = APIRouter(
    prefix="/wealth-dna",
    tags=["Wealth DNA"],
)


@router.post(
    "/generate",
    response_model=WealthDNAResponse,
    status_code=status.HTTP_200_OK,
)
def generate(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return generate_wealth_dna(
            db=db,
            user_id=current_user.id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.get(
    "",
    response_model=WealthDNAResponse,
    status_code=status.HTTP_200_OK,
)
def get_dna(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return get_wealth_dna(
            db=db,
            user_id=current_user.id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
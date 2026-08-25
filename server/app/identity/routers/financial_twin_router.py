from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user

from app.identity.schemas.financial_twin import (
    FinancialTwinResponse,
)

from app.identity.services.financial_twin_service import (
    get_financial_twin,
)


router = APIRouter(
    prefix="/financial-twin",
    tags=["Financial Twin"],
)


@router.get(
    "",
    response_model=FinancialTwinResponse,
    status_code=status.HTTP_200_OK,
)
def financial_twin(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return get_financial_twin(
            db=db,
            user_id=current_user.id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
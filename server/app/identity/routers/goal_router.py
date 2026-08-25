from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user

from app.identity.schemas.goal import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
)

from app.identity.services.goal_service import (
    create_goal,
    get_goals,
    get_goal,
    update_goal,
    delete_goal,
)


router = APIRouter(
    prefix="/goals",
    tags=["Goals"],
)


@router.post(
    "",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_goal(
    data: GoalCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return create_goal(
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
    response_model=list[GoalResponse],
)
def list_goals(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_goals(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{goal_id}",
    response_model=GoalResponse,
)
def get_single_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return get_goal(
            db=db,
            user_id=current_user.id,
            goal_id=goal_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.put(
    "/{goal_id}",
    response_model=GoalResponse,
)
def update_existing_goal(
    goal_id: int,
    data: GoalUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return update_goal(
            db=db,
            user_id=current_user.id,
            goal_id=goal_id,
            data=data,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_200_OK,
)
def delete_existing_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return delete_goal(
            db=db,
            user_id=current_user.id,
            goal_id=goal_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
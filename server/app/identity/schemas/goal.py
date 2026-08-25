from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    goal_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    goal_type: str = Field(
        default="CUSTOM",
        max_length=50,
    )

    target_amount: float = Field(
        ...,
        gt=0,
    )

    current_amount: float = Field(
        default=0,
        ge=0,
    )

    target_date: date

    monthly_contribution: float = Field(
        default=0,
        ge=0,
    )

    priority: int = Field(
        default=3,
        ge=1,
        le=5,
    )


class GoalUpdate(BaseModel):
    goal_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    goal_type: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    target_amount: Optional[float] = Field(
        default=None,
        gt=0,
    )

    current_amount: Optional[float] = Field(
        default=None,
        ge=0,
    )

    target_date: Optional[date] = None

    monthly_contribution: Optional[float] = Field(
        default=None,
        ge=0,
    )

    priority: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
    )

    status: Optional[str] = Field(
        default=None,
        max_length=30,
    )


class GoalResponse(BaseModel):
    id: int
    user_id: int

    goal_name: str
    goal_type: str

    target_amount: float
    current_amount: float

    target_date: date
    monthly_contribution: float

    priority: int

    progress_percentage: float
    required_monthly_investment: float
    months_remaining: int

    status: str

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
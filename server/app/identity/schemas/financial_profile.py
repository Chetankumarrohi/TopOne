from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FinancialProfileBase(BaseModel):
    annual_income: float = Field(default=0, ge=0)
    monthly_income: float = Field(default=0, ge=0)
    monthly_expenses: float = Field(default=0, ge=0)
    monthly_debt_payment: float = Field(default=0, ge=0)

    total_savings: float = Field(default=0, ge=0)
    emergency_fund: float = Field(default=0, ge=0)

    total_assets: float = Field(default=0, ge=0)
    total_liabilities: float = Field(default=0, ge=0)

    existing_investments: float = Field(default=0, ge=0)
    insurance_cover: float = Field(default=0, ge=0)


class FinancialProfileCreate(FinancialProfileBase):
    pass


class FinancialProfileUpdate(BaseModel):
    annual_income: Optional[float] = Field(default=None, ge=0)
    monthly_income: Optional[float] = Field(default=None, ge=0)
    monthly_expenses: Optional[float] = Field(default=None, ge=0)
    monthly_debt_payment: Optional[float] = Field(default=None, ge=0)

    total_savings: Optional[float] = Field(default=None, ge=0)
    emergency_fund: Optional[float] = Field(default=None, ge=0)

    total_assets: Optional[float] = Field(default=None, ge=0)
    total_liabilities: Optional[float] = Field(default=None, ge=0)

    existing_investments: Optional[float] = Field(default=None, ge=0)
    insurance_cover: Optional[float] = Field(default=None, ge=0)


class FinancialProfileResponse(FinancialProfileBase):
    id: int
    user_id: int

    # Backend-calculated values
    net_worth: float
    savings_rate: float
    debt_to_income_ratio: float
    emergency_months: float
    investment_ratio: float

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
from datetime import date
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    holding_id: Optional[int] = Field(None, description="Optional ID of existing investment holding")
    asset_type: str = Field("MUTUAL_FUND", description="MUTUAL_FUND, STOCK, ETF, GOLD, BOND, PPF, EPF, NPS, CASH, OTHER")
    asset_name: str = Field(..., description="Name of the asset/scheme")
    symbol: Optional[str] = Field(None, description="Ticker symbol if applicable")
    isin: Optional[str] = Field(None, description="ISIN number if applicable")
    transaction_type: str = Field(..., description="BUY, SELL, SIP, REDEMPTION, DIVIDEND, BONUS, SPLIT, SWITCH_IN, SWITCH_OUT, FEE")
    quantity: float = Field(0.0, ge=0.0, description="Quantity or number of units")
    price: float = Field(0.0, ge=0.0, description="Price per unit / NAV")
    gross_amount: Optional[float] = Field(None, ge=0.0, description="Gross transaction amount. Calculated if omitted.")
    fees: float = Field(0.0, ge=0.0, description="Brokerage / transaction fees")
    taxes: float = Field(0.0, ge=0.0, description="STT / GST / taxes")
    transaction_date: Optional[date] = Field(None, description="Date of transaction (defaults to today)")
    source: str = Field("MANUAL", description="MANUAL, CAS_IMPORT, BROKER, RTA, SYSTEM")
    external_reference: Optional[str] = Field(None, description="External reference key for idempotency protection")
    notes: Optional[str] = Field(None, description="Optional notes or remarks")


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    holding_id: Optional[int] = None
    asset_type: str
    asset_name: str
    symbol: Optional[str] = None
    isin: Optional[str] = None
    transaction_type: str
    quantity: float
    price: float
    gross_amount: float
    fees: float
    taxes: float
    net_amount: float
    transaction_date: str
    source: str
    external_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[TransactionResponse]


class ReconcilePortfolioResponse(BaseModel):
    message: str
    user_id: int
    processed_holdings: int
    total_transactions: int
    status: str

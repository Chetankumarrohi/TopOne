from pydantic import BaseModel


class AssetAllocationItem(BaseModel):
    asset_type: str
    value: float
    percentage: float


class PortfolioSummaryResponse(BaseModel):
    total_invested: float
    current_value: float

    total_gain: float
    total_gain_percentage: float

    number_of_holdings: int

    mutual_fund_value: float
    stock_value: float
    etf_value: float
    gold_value: float
    debt_value: float
    other_value: float

    asset_allocation: list[AssetAllocationItem]
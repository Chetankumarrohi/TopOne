from datetime import date

from pydantic import BaseModel, ConfigDict


class FundNAVHistoryResponse(BaseModel):
    id: int
    product_id: int

    nav_date: date
    nav: float

    daily_change: float | None
    daily_change_percentage: float | None

    model_config = ConfigDict(
        from_attributes=True
    )
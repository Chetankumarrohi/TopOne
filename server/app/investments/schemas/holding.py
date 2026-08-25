from pydantic import BaseModel, Field


class HoldingCreate(BaseModel):
    asset_type: str = Field(
        ...,
        min_length=2,
        max_length=30,
    )

    asset_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    symbol: str | None = None
    isin: str | None = None
    provider: str | None = None

    quantity: float = Field(
        default=0,
        ge=0,
    )

    average_buy_price: float = Field(
        default=0,
        ge=0,
    )

    invested_amount: float = Field(
        ...,
        ge=0,
    )

    current_price: float = Field(
        default=0,
        ge=0,
    )

    current_value: float = Field(
        ...,
        ge=0,
    )

    asset_class: str | None = None
    category: str | None = None
    sector: str | None = None
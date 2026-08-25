from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user

from app.investments.models.holding import (
    InvestmentHolding,
)

from app.investments.schemas.portfolio import (
    PortfolioSummaryResponse,
)

from app.investments.schemas.holding import (
    HoldingCreate,
)

from app.investments.services.portfolio_service import (
    get_portfolio_summary,
)

from app.investments.services.portfolio_snapshot_service import (
    get_portfolio_history,
)



router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


# ---------------------------------------------------------
# Portfolio Summary
# ---------------------------------------------------------

@router.get(
    "/summary",
    response_model=PortfolioSummaryResponse,
    status_code=status.HTTP_200_OK,
)
def portfolio_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_portfolio_summary(
        db=db,
        user_id=current_user.id,
    )


# ---------------------------------------------------------
# Portfolio Holdings
# ---------------------------------------------------------

@router.get(
    "/holdings",
    status_code=status.HTTP_200_OK,
)
def portfolio_holdings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    holdings = (
        db.query(InvestmentHolding)
        .filter(
            InvestmentHolding.user_id
            == current_user.id
        )
        .order_by(
            InvestmentHolding.current_value.desc()
        )
        .all()
    )

    return [
        {
            "id": holding.id,

            "asset_type":
                holding.asset_type,

            "asset_name":
                holding.asset_name,

            "symbol":
                holding.symbol,

            "isin":
                holding.isin,

            "provider":
                holding.provider,

            "folio_number_masked":
                holding.folio_number_masked,

            "quantity":
                holding.quantity,

            "average_buy_price":
                holding.average_buy_price,

            "invested_amount":
                holding.invested_amount,

            "current_price":
                holding.current_price,

            "current_value":
                holding.current_value,

            "total_gain":
                holding.total_gain,

            "total_gain_percentage":
                holding.total_gain_percentage,

            "asset_class":
                holding.asset_class,

            "category":
                holding.category,

            "sector":
                holding.sector,

            "source":
                holding.source,

            "sync_status":
                holding.sync_status,
        }
        for holding in holdings
    ]


# ---------------------------------------------------------
# Add Holding Manually
# ---------------------------------------------------------

@router.post(
    "/holdings",
    status_code=status.HTTP_201_CREATED,
)
def create_holding(
    data: HoldingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    asset_type = (
        data.asset_type.upper()
    )

    total_gain = (
        data.current_value
        - data.invested_amount
    )

    if data.invested_amount > 0:
        total_gain_percentage = (
            total_gain
            / data.invested_amount
        ) * 100
    else:
        total_gain_percentage = 0

    holding = InvestmentHolding(
        user_id=current_user.id,

        asset_type=asset_type,

        asset_name=data.asset_name,

        symbol=data.symbol,

        isin=data.isin,

        provider=data.provider,

        quantity=data.quantity,

        average_buy_price=
            data.average_buy_price,

        invested_amount=
            data.invested_amount,

        current_price=
            data.current_price,

        current_value=
            data.current_value,

        total_gain=round(
            total_gain,
            2,
        ),

        total_gain_percentage=round(
            total_gain_percentage,
            2,
        ),

        asset_class=(
            data.asset_class.upper()
            if data.asset_class
            else None
        ),

        category=data.category,

        sector=data.sector,

        source="MANUAL",

        sync_status="ACTIVE",
    )

    db.add(holding)
    db.commit()
    db.refresh(holding)

    return {
        "message":
            "Investment added successfully.",

        "holding_id":
            holding.id,

        "asset_name":
            holding.asset_name,

        "current_value":
            holding.current_value,

        "total_gain":
            holding.total_gain,

        "total_gain_percentage":
            holding.total_gain_percentage,
    }


# ---------------------------------------------------------
# Delete Holding
# ---------------------------------------------------------

@router.delete(
    "/holdings/{holding_id}",
    status_code=status.HTTP_200_OK,
)
def delete_holding(
    holding_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    holding = (
        db.query(InvestmentHolding)
        .filter(
            InvestmentHolding.id
            == holding_id,

            InvestmentHolding.user_id
            == current_user.id,
        )
        .first()
    )

    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment holding not found.",
        )

    db.delete(holding)
    db.commit()

    return {
        "message":
            "Investment removed successfully."
    }


# ---------------------------------------------------------
# Portfolio History
# ---------------------------------------------------------

@router.get(
    "/history",
    status_code=status.HTTP_200_OK,
)
def portfolio_history(
    range: str = Query("1M", description="Time range: 1M, 3M, 6M, 1Y, ALL"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_portfolio_history(
        db=db,
        user_id=current_user.id,
        range_param=range,
    )
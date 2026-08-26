from datetime import date
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.investments.models.holding import InvestmentHolding
from app.investments.models.portfolio_transaction import PortfolioTransaction
from app.investments.schemas.holding import HoldingCreate
from app.investments.schemas.portfolio import PortfolioSummaryResponse
from app.investments.schemas.transaction import (
    ReconcilePortfolioResponse,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
)
from app.investments.services.portfolio_service import get_portfolio_summary
from app.investments.services.portfolio_snapshot_service import get_portfolio_history
from app.investments.services.portfolio_transaction_service import (
    get_transaction_by_id,
    get_user_transactions,
    reconcile_user_portfolio_ledger,
    record_transaction,
)
from app.investments.services.portfolio_valuation_service import value_user_portfolio

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
        .filter(InvestmentHolding.user_id == current_user.id)
        .order_by(InvestmentHolding.current_value.desc())
        .all()
    )

    return [
        {
            "id": holding.id,
            "asset_type": holding.asset_type,
            "asset_name": holding.asset_name,
            "symbol": holding.symbol,
            "isin": holding.isin,
            "provider": holding.provider,
            "folio_number_masked": holding.folio_number_masked,
            "quantity": holding.quantity,
            "average_buy_price": holding.average_buy_price,
            "invested_amount": holding.invested_amount,
            "current_price": holding.current_price,
            "current_value": holding.current_value,
            "total_gain": holding.total_gain,
            "total_gain_percentage": holding.total_gain_percentage,
            "asset_class": holding.asset_class,
            "category": holding.category,
            "sector": holding.sector,
            "source": holding.source,
            "sync_status": holding.sync_status,
        }
        for holding in holdings
    ]


# ---------------------------------------------------------
# Add Holding Manually (Creates Holding + Initial Ledger Entry)
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
    asset_type = data.asset_type.upper()
    total_gain = data.current_value - data.invested_amount

    if data.invested_amount > 0:
        total_gain_percentage = (total_gain / data.invested_amount) * 100
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
        average_buy_price=data.average_buy_price,
        invested_amount=data.invested_amount,
        current_price=data.current_price,
        current_value=data.current_value,
        total_gain=round(total_gain, 2),
        total_gain_percentage=round(total_gain_percentage, 2),
        asset_class=data.asset_class.upper() if data.asset_class else None,
        category=data.category,
        sector=data.sector,
        source="MANUAL",
        sync_status="ACTIVE",
    )

    db.add(holding)
    db.flush()

    # Automatically record an initial BUY transaction entry in the immutable ledger
    if holding.quantity > 0:
        gross = holding.quantity * holding.average_buy_price
        init_tx = PortfolioTransaction(
            user_id=current_user.id,
            holding_id=holding.id,
            asset_type=holding.asset_type,
            asset_name=holding.asset_name,
            symbol=holding.symbol,
            isin=holding.isin,
            transaction_type="BUY",
            quantity=holding.quantity,
            price=holding.average_buy_price,
            gross_amount=round(gross, 2),
            fees=0.0,
            taxes=0.0,
            net_amount=round(holding.invested_amount or gross, 2),
            transaction_date=date.today(),
            source="MANUAL",
            external_reference=f"MANUAL-HOLDING-{holding.id}",
            notes="Initial manual holding entry",
        )
        db.add(init_tx)

    db.commit()
    db.refresh(holding)

    return {
        "message": "Investment added successfully.",
        "holding_id": holding.id,
        "asset_name": holding.asset_name,
        "current_value": holding.current_value,
        "total_gain": holding.total_gain,
        "total_gain_percentage": holding.total_gain_percentage,
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
            InvestmentHolding.id == holding_id,
            InvestmentHolding.user_id == current_user.id,
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

    return {"message": "Investment removed successfully."}


# ---------------------------------------------------------
# Portfolio Revaluation
# ---------------------------------------------------------

@router.post(
    "/revalue",
    status_code=status.HTTP_200_OK,
)
def revalue_portfolio(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return value_user_portfolio(
        db=db,
        user_id=current_user.id,
    )


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


# ---------------------------------------------------------
# Portfolio Transactions Ledger
# ---------------------------------------------------------

@router.post(
    "/transactions",
    status_code=status.HTTP_201_CREATED,
)
def create_portfolio_transaction(
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return record_transaction(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get(
    "/transactions",
    status_code=status.HTTP_200_OK,
)
def list_portfolio_transactions(
    holding_id: Optional[int] = Query(None, description="Filter by holding ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    isin: Optional[str] = Query(None, description="Filter by ISIN"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    start_date: Optional[date] = Query(None, description="Filter from transaction date"),
    end_date: Optional[date] = Query(None, description="Filter to transaction date"),
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_user_transactions(
        db=db,
        user_id=current_user.id,
        holding_id=holding_id,
        symbol=symbol,
        isin=isin,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/transactions/reconcile",
    response_model=ReconcilePortfolioResponse,
    status_code=status.HTTP_200_OK,
)
def reconcile_portfolio_transactions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return reconcile_user_portfolio_ledger(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/transactions/{transaction_id}",
    status_code=status.HTTP_200_OK,
)
def get_portfolio_transaction_detail(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_transaction_by_id(
        db=db,
        user_id=current_user.id,
        transaction_id=transaction_id,
    )
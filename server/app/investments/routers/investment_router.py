import requests

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from app.investments.schemas.investment import (
    InvestmentProductResponse,
    InvestmentOrderCreate,
    InvestmentOrderResponse,
    FundPeerComparisonResponse,
)
from app.investments.services.peer_comparison_service import (
    calculate_peer_comparison,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user

from app.investments.models.investment_product import (
    InvestmentProduct,
)

from app.investments.models.investment_order import (
    InvestmentOrder,
)

from app.investments.models.fund_nav_history import (
    FundNAVHistory,
)

from app.investments.models.fund_health_history import (
    FundHealthHistory,
)

from app.investments.schemas.investment import (
    InvestmentProductResponse,
    InvestmentOrderCreate,
    InvestmentOrderResponse,
)

from app.investments.schemas.nav_history import (
    FundNAVHistoryResponse,
)

from app.investments.schemas.fund_health_history import (
    FundHealthHistoryResponse,
)

from app.investments.services.amfi_fund_master_service import (
    sync_amfi_fund_master,
)

from app.investments.services.amfi_historical_nav_service import (
    sync_historical_nav,
)

from app.investments.services.fund_analytics_service import (
    calculate_fund_analytics,
    update_product_analytics,
)


router = APIRouter(
    prefix="/investments",
    tags=["Investments"],
)


# ---------------------------------------------------------
# PRODUCT CATALOG
# ---------------------------------------------------------

@router.get(
    "/products",
    response_model=list[InvestmentProductResponse],
    status_code=status.HTTP_200_OK,
)
def list_products(
    category: str | None = Query(
        default=None,
    ),
    product_type: str | None = Query(
        default=None,
    ),
    risk_level: str | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = (
        db.query(InvestmentProduct)
        .filter(
            InvestmentProduct.is_active
            == True
        )
    )

    if category:
        query = query.filter(
            InvestmentProduct.category
            == category
        )

    if product_type:
        query = query.filter(
            InvestmentProduct.product_type
            == product_type.upper()
        )

    if risk_level:
        query = query.filter(
            InvestmentProduct.risk_level
            == risk_level
        )

    products = (
        query
        .order_by(
            InvestmentProduct.name.asc()
        )
        .all()
    )

    return products


# ---------------------------------------------------------
# PRODUCT DETAILS
# ---------------------------------------------------------

@router.get(
    "/products/{product_id}",
    response_model=InvestmentProductResponse,
    status_code=status.HTTP_200_OK,
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    product = (
        db.query(InvestmentProduct)
        .filter(
            InvestmentProduct.id
            == product_id,

            InvestmentProduct.is_active
            == True,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment product not found.",
        )

    return product


# ---------------------------------------------------------
# NAV HISTORY
# ---------------------------------------------------------

@router.get(
    "/products/{product_id}/nav-history",
    response_model=list[FundNAVHistoryResponse],
    status_code=status.HTTP_200_OK,
)
def get_nav_history(
    product_id: int,
    days: int | None = Query(
        default=None,
        ge=1,
        le=3650,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    product = (
        db.query(InvestmentProduct)
        .filter(
            InvestmentProduct.id
            == product_id,

            InvestmentProduct.is_active
            == True,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment product not found.",
        )

    query = (
        db.query(FundNAVHistory)
        .filter(
            FundNAVHistory.product_id
            == product_id
        )
        .order_by(
            FundNAVHistory.nav_date.desc()
        )
    )

    if days:
        history = (
            query
            .limit(days)
            .all()
        )
    else:
        history = query.all()

    return list(
        reversed(history)
    )


# ---------------------------------------------------------
# FUND HEALTH HISTORY
# ---------------------------------------------------------

@router.get(
    "/products/{product_id}/health-history",
    response_model=list[FundHealthHistoryResponse],
    status_code=status.HTTP_200_OK,
)
def get_fund_health_history(
    product_id: int,
    limit: int = Query(
        default=365,
        ge=1,
        le=3650,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    product = (
        db.query(InvestmentProduct)
        .filter(
            InvestmentProduct.id
            == product_id,

            InvestmentProduct.is_active
            == True,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment product not found.",
        )

    rows = (
        db.query(FundHealthHistory)
        .filter(
            FundHealthHistory.product_id
            == product_id
        )
        .order_by(
            FundHealthHistory.snapshot_date.desc()
        )
        .limit(limit)
        .all()
    )

    return list(
        reversed(rows)
    )


# ---------------------------------------------------------
# AMFI LIVE FUND MASTER + DAILY NAV SYNC
# ---------------------------------------------------------

@router.post(
    "/admin/sync-amfi",
    status_code=status.HTTP_200_OK,
)
def sync_amfi(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return sync_amfi_fund_master(
            db=db
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Could not fetch the latest "
                "NAV data from AMFI."
            ),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"AMFI sync failed: {str(error)}"
            ),
        )


# ---------------------------------------------------------
# AMFI HISTORICAL NAV SYNC
# ---------------------------------------------------------

@router.post(
    "/admin/sync-amfi-history",
    status_code=status.HTTP_200_OK,
)
def sync_amfi_history(
    months: int = Query(
        default=12,
        ge=1,
        le=60,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return sync_historical_nav(
            db=db,
            months=months,
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Could not fetch historical "
                "NAV data from AMFI."
            ),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Historical NAV sync failed: "
                f"{str(error)}"
            ),
        )


# ---------------------------------------------------------
# FUND ANALYTICS
# ---------------------------------------------------------

@router.get(
    "/products/{product_id}/analytics",
    status_code=status.HTTP_200_OK,
)
def get_product_analytics(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    product = (
        db.query(InvestmentProduct)
        .filter(
            InvestmentProduct.id == product_id,
            InvestmentProduct.is_active == True,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment product not found.",
        )

    return calculate_fund_analytics(
        db=db,
        product=product,
    )


@router.post(
    "/products/{product_id}/analytics/update",
    status_code=status.HTTP_200_OK,
)
def refresh_product_analytics(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    product = (
        db.query(InvestmentProduct)
        .filter(
            InvestmentProduct.id == product_id,
            InvestmentProduct.is_active == True,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment product not found.",
        )

    analytics = update_product_analytics(
        db=db,
        product=product,
    )

    db.commit()

    return {
        "message": "Fund analytics updated successfully.",
        "analytics": analytics,
    }
# ---------------------------------------------------------
# CATEGORY PEER COMPARISON
# ---------------------------------------------------------

@router.get(
    "/products/{product_id}/peer-comparison",
    response_model=FundPeerComparisonResponse,
    status_code=status.HTTP_200_OK,
)
def get_product_peer_comparison(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    product = (
        db.query(InvestmentProduct)
        .filter(
            InvestmentProduct.id == product_id,
            InvestmentProduct.is_active == True,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment product not found.",
        )

    return calculate_peer_comparison(
        db=db,
        product=product,
    )

# ---------------------------------------------------------
# BULK FUND ANALYTICS
# ---------------------------------------------------------

@router.post(
    "/admin/update-fund-analytics",
    status_code=status.HTTP_200_OK,
)
def update_all_fund_analytics(
    limit: int = Query(
        default=100,
        ge=1,
        le=5000,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    products = (
        db.query(InvestmentProduct)
        .filter(
            InvestmentProduct.is_active == True,
            InvestmentProduct.source == "AMFI",
        )
        .order_by(
            InvestmentProduct.id.asc()
        )
        .limit(limit)
        .all()
    )

    processed = 0
    updated = 0
    insufficient_history = 0
    failed = 0

    for product in products:
        processed += 1

        try:
            result = update_product_analytics(
                db=db,
                product=product,
            )

            if result.get("status") == "INSUFFICIENT_HISTORY":
                insufficient_history += 1
            else:
                updated += 1

        except Exception:
            failed += 1

    db.commit()

    return {
        "processed": processed,
        "updated": updated,
        "insufficient_history": insufficient_history,
        "failed": failed,
    }


# ---------------------------------------------------------
# CREATE INVESTMENT ORDER
# ---------------------------------------------------------

@router.post(
    "/orders",
    response_model=InvestmentOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    data: InvestmentOrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    product = (
        db.query(InvestmentProduct)
        .filter(
            InvestmentProduct.id
            == data.product_id,

            InvestmentProduct.is_active
            == True,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment product not found.",
        )

    mode = (
        data.investment_mode.upper()
    )

    if mode not in {
        "LUMPSUM",
        "SIP",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Investment mode must be "
                "LUMPSUM or SIP."
            ),
        )

    # --------------------------------
    # LUMPSUM VALIDATION
    # --------------------------------

    if mode == "LUMPSUM":

        if not product.purchase_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Lumpsum investment is "
                    "not available for this product."
                ),
            )

        if (
            product.minimum_lumpsum > 0
            and data.amount
            < product.minimum_lumpsum
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Minimum lumpsum amount is "
                    f"₹{product.minimum_lumpsum:.0f}."
                ),
            )

    # --------------------------------
    # SIP VALIDATION
    # --------------------------------

    if mode == "SIP":

        if not product.sip_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "SIP is not available "
                    "for this product."
                ),
            )

        if (
            product.minimum_sip > 0
            and data.amount
            < product.minimum_sip
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Minimum SIP amount is "
                    f"₹{product.minimum_sip:.0f}."
                ),
            )

    # --------------------------------
    # CREATE INTERNAL ORDER
    # --------------------------------

    order = InvestmentOrder(
        user_id=current_user.id,

        product_id=product.id,

        transaction_type="PURCHASE",

        investment_mode=mode,

        amount=data.amount,

        status="PENDING",

        execution_provider=None,

        provider_order_id=None,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


# ---------------------------------------------------------
# USER ORDER HISTORY
# ---------------------------------------------------------

@router.get(
    "/orders",
    response_model=list[InvestmentOrderResponse],
    status_code=status.HTTP_200_OK,
)
def list_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return (
        db.query(InvestmentOrder)
        .filter(
            InvestmentOrder.user_id
            == current_user.id
        )
        .order_by(
            InvestmentOrder.created_at.desc()
        )
        .all()
    )


# ---------------------------------------------------------
# SINGLE ORDER
# ---------------------------------------------------------

@router.get(
    "/orders/{order_id}",
    response_model=InvestmentOrderResponse,
    status_code=status.HTTP_200_OK,
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order = (
        db.query(InvestmentOrder)
        .filter(
            InvestmentOrder.id
            == order_id,

            InvestmentOrder.user_id
            == current_user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment order not found.",
        )

    return order

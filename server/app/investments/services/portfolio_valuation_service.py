from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.investments.models.fund_nav_history import FundNAVHistory
from app.investments.models.holding import InvestmentHolding
from app.investments.models.investment_product import InvestmentProduct
from app.investments.services.portfolio_service import get_portfolio_summary

STALE_THRESHOLD_DAYS = 7


def get_latest_price_for_holding(
    db: Session,
    holding: InvestmentHolding,
) -> Tuple[float, Optional[date], str]:
    """
    Resolves the latest market price/NAV, price date, and valuation source for a given holding.
    Supports Mutual Funds, Stocks, ETFs, Gold, Bonds, etc.
    Gracefully handles missing prices by falling back to current_price or average_buy_price.
    """
    asset_type = (holding.asset_type or "OTHER").upper()

    # 1. Mutual Fund NAV Resolution
    if asset_type == "MUTUAL_FUND":
        product: Optional[InvestmentProduct] = None

        if holding.isin:
            product = (
                db.query(InvestmentProduct)
                .filter(InvestmentProduct.isin == holding.isin)
                .first()
            )

        if not product and holding.symbol:
            product = (
                db.query(InvestmentProduct)
                .filter(InvestmentProduct.symbol == holding.symbol)
                .first()
            )

        if not product and holding.asset_name:
            product = (
                db.query(InvestmentProduct)
                .filter(InvestmentProduct.name == holding.asset_name)
                .first()
            )

        if product and product.nav and product.nav > 0:
            nav_d = product.nav_date or date.today()
            return float(product.nav), nav_d, "AMFI_NAV"

        # Fallback to FundNAVHistory if product has historical NAV record
        if product:
            nav_hist = (
                db.query(FundNAVHistory)
                .filter(FundNAVHistory.product_id == product.id)
                .order_by(FundNAVHistory.nav_date.desc())
                .first()
            )
            if nav_hist and nav_hist.nav > 0:
                return float(nav_hist.nav), nav_hist.nav_date, "AMFI_HISTORICAL_NAV"

    # 2. Stock / ETF / Gold / Bond Quote Resolution
    if holding.current_price and holding.current_price > 0:
        return float(holding.current_price), date.today(), "MARKET_QUOTE"

    if holding.average_buy_price and holding.average_buy_price > 0:
        return float(holding.average_buy_price), date.today(), "FALLBACK_COST_PRICE"

    return 0.0, date.today(), "FALLBACK_ZERO"


def value_holding(
    db: Session,
    holding: InvestmentHolding,
) -> Dict[str, Any]:
    """
    Calculates dynamic valuation for a single holding.
    NEVER overwrites cost basis (average_buy_price, invested_amount).
    Updates current_price, current_value, total_gain, total_gain_percentage, and sync_status.
    """
    latest_price, price_date, source = get_latest_price_for_holding(db, holding)

    # Stale Price Detection
    is_stale = False
    if price_date:
        days_old = (date.today() - price_date).days
        if days_old > STALE_THRESHOLD_DAYS:
            is_stale = True

    qty = float(holding.quantity or 0.0)
    invested = float(holding.invested_amount or 0.0)

    current_val = round(qty * latest_price, 2)
    gain = round(current_val - invested, 2)

    if invested > 0:
        gain_pct = round((gain / invested) * 100, 2)
    else:
        gain_pct = 0.0

    holding.current_price = round(latest_price, 2)
    holding.current_value = current_val
    holding.total_gain = gain
    holding.total_gain_percentage = gain_pct

    if is_stale:
        holding.sync_status = "STALE"
    else:
        holding.sync_status = "ACTIVE"

    return {
        "holding_id": holding.id,
        "asset_name": holding.asset_name,
        "quantity": qty,
        "invested_amount": invested,
        "average_buy_price": holding.average_buy_price,
        "current_price": holding.current_price,
        "current_value": holding.current_value,
        "total_gain": holding.total_gain,
        "total_gain_percentage": holding.total_gain_percentage,
        "price_as_of": str(price_date) if price_date else None,
        "valuation_source": source,
        "is_stale": is_stale,
        "sync_status": holding.sync_status,
    }


def value_user_portfolio(
    db: Session,
    user_id: int,
) -> Dict[str, Any]:
    """
    Revalues all active holdings for an authenticated user and updates portfolio metrics.
    Cost basis (invested_amount, average_buy_price) is strictly preserved.
    """
    holdings = (
        db.query(InvestmentHolding)
        .filter(InvestmentHolding.user_id == user_id)
        .all()
    )

    valued_holdings = []
    for holding in holdings:
        res = value_holding(db, holding)
        valued_holdings.append(res)

    db.commit()

    summary = get_portfolio_summary(db, user_id)

    return {
        "user_id": user_id,
        "holdings_count": len(holdings),
        "total_invested": summary.get("total_invested", 0.0),
        "current_value": summary.get("current_value", 0.0),
        "total_gain": summary.get("total_gain", 0.0),
        "total_gain_percentage": summary.get("total_gain_percentage", 0.0),
        "valued_holdings": valued_holdings,
        "status": "success",
    }


def value_all_portfolios_batch(
    db: Session,
) -> Dict[str, Any]:
    """
    Batch job to revalue holdings for all active users across the platform.
    Runs prior to daily portfolio snapshot creation.
    """
    user_ids_query = (
        db.query(InvestmentHolding.user_id)
        .distinct()
        .all()
    )
    user_ids = [row[0] for row in user_ids_query if row[0] is not None]

    processed_users = 0
    total_holdings_valued = 0

    for uid in user_ids:
        res = value_user_portfolio(db, uid)
        processed_users += 1
        total_holdings_valued += res.get("holdings_count", 0)

    return {
        "processed_users": processed_users,
        "total_holdings_valued": total_holdings_valued,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }

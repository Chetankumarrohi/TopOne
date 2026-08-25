from datetime import date, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.investments.models.portfolio_snapshot import PortfolioSnapshot
from app.investments.services.portfolio_service import get_portfolio_summary


RANGE_DAYS_MAP = {
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "1Y": 365,
}


def create_or_update_portfolio_snapshot(
    db: Session,
    user_id: int,
    snapshot_date: Optional[date] = None,
) -> dict[str, Any]:
    """
    Creates or updates the daily portfolio snapshot for a given user.
    Operation is idempotent per (user_id, snapshot_date).
    """
    target_date = snapshot_date or date.today()

    summary = get_portfolio_summary(db, user_id)

    invested_value = float(summary.get("total_invested", 0.0) or 0.0)
    market_value = float(summary.get("current_value", 0.0) or 0.0)
    pnl = round(market_value - invested_value, 2)

    if invested_value > 0:
        pnl_percentage = round((pnl / invested_value) * 100, 2)
    else:
        pnl_percentage = 0.0

    snapshot = (
        db.query(PortfolioSnapshot)
        .filter(
            PortfolioSnapshot.user_id == user_id,
            PortfolioSnapshot.snapshot_date == target_date,
        )
        .first()
    )

    if snapshot:
        snapshot.market_value = market_value
        snapshot.invested_value = invested_value
        snapshot.pnl = pnl
        snapshot.pnl_percentage = pnl_percentage
    else:
        snapshot = PortfolioSnapshot(
            user_id=user_id,
            snapshot_date=target_date,
            market_value=market_value,
            invested_value=invested_value,
            pnl=pnl,
            pnl_percentage=pnl_percentage,
        )
        db.add(snapshot)

    db.commit()
    db.refresh(snapshot)

    return {
        "snapshot_date": str(snapshot.snapshot_date),
        "market_value": snapshot.market_value,
        "invested_value": snapshot.invested_value,
        "pnl": snapshot.pnl,
        "pnl_percentage": snapshot.pnl_percentage,
    }


def get_portfolio_history(
    db: Session,
    user_id: int,
    range_param: str = "1M",
) -> list[dict[str, Any]]:
    """
    Retrieves historical portfolio snapshot records for a user filtered by range.
    Supported ranges: 1M, 3M, 6M, 1Y, ALL.
    Returns list of items ordered ascending by snapshot_date.
    """
    range_clean = (range_param or "1M").upper().strip()

    query = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user_id
    )

    if range_clean != "ALL":
        days = RANGE_DAYS_MAP.get(range_clean, 30)
        cutoff_date = date.today() - timedelta(days=days)
        query = query.filter(PortfolioSnapshot.snapshot_date >= cutoff_date)

    snapshots = query.order_by(PortfolioSnapshot.snapshot_date.asc()).all()

    return [
        {
            "date": str(s.snapshot_date),
            "market_value": s.market_value,
            "invested_value": s.invested_value,
            "pnl": s.pnl,
            "pnl_percentage": s.pnl_percentage,
        }
        for s in snapshots
    ]

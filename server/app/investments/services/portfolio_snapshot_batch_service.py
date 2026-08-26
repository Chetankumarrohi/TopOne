from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.investments.models.holding import InvestmentHolding
from app.investments.services.portfolio_snapshot_service import (
    create_or_update_portfolio_snapshot,
)
from app.investments.services.portfolio_valuation_service import (
    value_all_portfolios_batch,
)
from app.users.model import User

logger = logging.getLogger(__name__)


def run_daily_portfolio_snapshots(db: Session) -> dict[str, Any]:
    """
    Batch service that creates/updates daily portfolio snapshots for all active
    users who have active investment holdings.
    Runs batch portfolio revaluation before snapshot capture.

    Per-user failure isolation ensures an error with one user's snapshot
    does not disrupt execution for other users.
    """
    start_time = time.time()

    # 1. Run batch valuation across all holdings first
    try:
        value_all_portfolios_batch(db)
    except Exception as exc:
        logger.exception("Error during batch valuation in daily portfolio pipeline: %s", exc)

    # Query active users who have at least one ACTIVE holding
    active_user_ids = (
        db.query(User.id)
        .join(InvestmentHolding, User.id == InvestmentHolding.user_id)
        .filter(
            User.is_active.is_(True),
            InvestmentHolding.sync_status == "ACTIVE",
        )
        .distinct()
        .all()
    )

    user_ids = [u[0] for u in active_user_ids]
    total_users = len(user_ids)

    processed = 0
    succeeded = 0
    failed = 0
    failures: list[dict[str, Any]] = []

    logger.info("Starting daily portfolio snapshot batch for %d user(s)...", total_users)

    for user_id in user_ids:
        processed += 1
        try:
            create_or_update_portfolio_snapshot(db, user_id=user_id)
            succeeded += 1
        except Exception as exc:
            failed += 1
            error_msg = str(exc)
            logger.exception("Failed to capture portfolio snapshot for user_id=%d", user_id)
            failures.append({
                "user_id": user_id,
                "error": error_msg,
            })

    duration_seconds = round(time.time() - start_time, 3)

    summary = {
        "total_users": total_users,
        "processed": processed,
        "succeeded": succeeded,
        "failed": failed,
        "failures": failures,
        "duration_seconds": duration_seconds,
    }

    logger.info(
        "Daily portfolio snapshot batch completed in %ss. total=%d succeeded=%d failed=%d",
        duration_seconds,
        total_users,
        succeeded,
        failed,
    )

    return summary

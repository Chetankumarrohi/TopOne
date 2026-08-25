from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.investments.models.investment_product import (
    InvestmentProduct,
)


HEALTHY_MAX_AGE_DAYS = 2
WARNING_MAX_AGE_DAYS = 4


def _utc_today() -> date:
    return datetime.now(
        timezone.utc
    ).date()


def get_latest_amfi_nav_date(
    db: Session,
) -> date | None:
    """
    Return the newest NAV date stored for active
    AMFI-backed products.
    """

    return (
        db.query(
            func.max(
                InvestmentProduct.nav_date
            )
        )
        .filter(
            InvestmentProduct.is_active == True,
            InvestmentProduct.source == "AMFI",
            InvestmentProduct.nav_date.isnot(None),
        )
        .scalar()
    )


def calculate_nav_age_days(
    latest_nav_date: date | None,
) -> int | None:
    if latest_nav_date is None:
        return None

    return (
        _utc_today()
        - latest_nav_date
    ).days


def determine_amfi_freshness(
    nav_age_days: int | None,
) -> tuple[str, list[str]]:
    reasons = []

    if nav_age_days is None:
        return (
            "CRITICAL",
            [
                "No AMFI NAV date is available."
            ],
        )

    if nav_age_days > WARNING_MAX_AGE_DAYS:
        return (
            "CRITICAL",
            [
                "AMFI NAV data is older than "
                f"{WARNING_MAX_AGE_DAYS} days."
            ],
        )

    if nav_age_days > HEALTHY_MAX_AGE_DAYS:
        return (
            "WARNING",
            [
                "AMFI NAV data is outside the normal "
                "freshness window."
            ],
        )

    return (
        "HEALTHY",
        [
            "AMFI NAV data is within the expected "
            "freshness window."
        ],
    )


def get_amfi_freshness_status(
    db: Session,
) -> dict[str, Any]:
    latest_nav_date = (
        get_latest_amfi_nav_date(
            db=db
        )
    )

    nav_age_days = (
        calculate_nav_age_days(
            latest_nav_date
        )
    )

    status, reasons = (
        determine_amfi_freshness(
            nav_age_days
        )
    )

    return {
        "status":
            status,

        "latest_nav_date":
            (
                latest_nav_date.isoformat()
                if latest_nav_date
                else None
            ),

        "nav_age_days":
            nav_age_days,

        "healthy_max_age_days":
            HEALTHY_MAX_AGE_DAYS,

        "warning_max_age_days":
            WARNING_MAX_AGE_DAYS,

        "reasons":
            reasons,
    }
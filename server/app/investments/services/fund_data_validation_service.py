from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.investments.models.investment_product import (
    InvestmentProduct,
)


# ============================================================
# VALIDATION LIMITS
# ============================================================

MAX_NAV_AGE_DAYS = 7

MIN_NAV = 0.0001
MAX_NAV = 10_000_000.0

MIN_EXPENSE_RATIO = 0.0
MAX_EXPENSE_RATIO = 5.0

MIN_AUM = 0.0

MIN_ALLOCATION = 0.0
MAX_ALLOCATION = 100.0

ALLOCATION_TOTAL_TOLERANCE = 5.0


# Lifecycle states that should be validated as current/live funds.
LIVE_SCHEME_STATUSES = {
    "ACTIVE",
}

# Historical/special lifecycle states are preserved in the database,
# but normal live-NAV freshness rules do not apply to them.
HISTORICAL_SCHEME_STATUSES = {
    "LEGACY",
    "SEGREGATED",
    "DEFUNCT",
    "MERGED",
    "CLOSED",
}

REVIEW_SCHEME_STATUSES = {
    "ZERO_NAV_REVIEW",
}


# ============================================================
# HELPERS
# ============================================================

def _percentage(
    value: int,
    total: int,
) -> float:
    if total <= 0:
        return 0.0

    return round(
        (value / total) * 100,
        2,
    )


def _issue(
    *,
    code: str,
    severity: str,
    message: str,
    product_id: int | None = None,
    field: str | None = None,
    value: Any = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "product_id": product_id,
        "field": field,
        "value": value,
    }


# ============================================================
# SINGLE PRODUCT VALIDATION
# ============================================================

def validate_product_data(
    product: InvestmentProduct,
) -> list[dict[str, Any]]:

    issues: list[
        dict[str, Any]
    ] = []

    scheme_status = (
        product.scheme_status
        or "ACTIVE"
    ).upper()

    is_live_scheme = (
        scheme_status
        in LIVE_SCHEME_STATUSES
    )

    # AMFI NAV freshness rules apply only to mutual funds.
    # ETFs, stocks, IPOs and other product types require
    # their own market-data validation pipelines.
    is_mutual_fund = (
        (product.product_type or "").upper()
        == "MUTUAL_FUND"
    )

    is_review_scheme = (
        scheme_status
        in REVIEW_SCHEME_STATUSES
    )

    # --------------------------------------------------------
    # NAV
    # --------------------------------------------------------

    # Full NAV bounds/freshness validation applies only to
    # schemes classified as currently live. Historical and
    # special schemes keep their data without generating false
    # live-feed alarms. ZERO_NAV_REVIEW remains visible through
    # an explicit review warning instead of INVALID_NAV.

    if (
        is_mutual_fund
        and is_live_scheme
    ):

        if product.nav is None:
            issues.append(
                _issue(
                    code="MISSING_NAV",
                    severity="CRITICAL",
                    message=(
                        "Active scheme has no current NAV."
                    ),
                    product_id=product.id,
                    field="nav",
                    value=product.nav,
                )
            )

        elif (
            product.nav < MIN_NAV
            or product.nav > MAX_NAV
        ):
            issues.append(
                _issue(
                    code="INVALID_NAV",
                    severity="CRITICAL",
                    message=(
                        "NAV is outside accepted bounds "
                        "for an active scheme."
                    ),
                    product_id=product.id,
                    field="nav",
                    value=product.nav,
                )
            )

        if product.nav_date is None:
            issues.append(
                _issue(
                    code="MISSING_NAV_DATE",
                    severity="CRITICAL",
                    message=(
                        "Active scheme has no NAV date."
                    ),
                    product_id=product.id,
                    field="nav_date",
                    value=None,
                )
            )

        else:
            nav_age = (
                date.today()
                - product.nav_date
            ).days

            if nav_age > MAX_NAV_AGE_DAYS:
                issues.append(
                    _issue(
                        code="STALE_NAV",
                        severity="WARNING",
                        message=(
                            f"Active scheme NAV is {nav_age} "
                            "days old."
                        ),
                        product_id=product.id,
                        field="nav_date",
                        value=product.nav_date,
                    )
                )

    elif (
        is_mutual_fund
        and is_review_scheme
    ):
        issues.append(
            _issue(
                code="ZERO_NAV_REVIEW",
                severity="WARNING",
                message=(
                    "Scheme is quarantined for zero/unavailable "
                    "NAV review and is not treated as a live "
                    "investable scheme."
                ),
                product_id=product.id,
                field="scheme_status",
                value=scheme_status,
            )
        )

    # --------------------------------------------------------
    # EXPENSE RATIO
    # --------------------------------------------------------

    if (
        product.expense_ratio
        is not None
    ):

        if (
            product.expense_ratio
            < MIN_EXPENSE_RATIO
            or product.expense_ratio
            > MAX_EXPENSE_RATIO
        ):
            issues.append(
                _issue(
                    code=(
                        "INVALID_EXPENSE_RATIO"
                    ),
                    severity="CRITICAL",
                    message=(
                        "Expense ratio is "
                        "outside accepted bounds."
                    ),
                    product_id=product.id,
                    field="expense_ratio",
                    value=(
                        product.expense_ratio
                    ),
                )
            )

    # --------------------------------------------------------
    # AUM
    # --------------------------------------------------------

    if (
        product.aum is not None
        and product.aum < MIN_AUM
    ):
        issues.append(
            _issue(
                code="INVALID_AUM",
                severity="CRITICAL",
                message=(
                    "AUM cannot be negative."
                ),
                product_id=product.id,
                field="aum",
                value=product.aum,
            )
        )

    # --------------------------------------------------------
    # ASSET ALLOCATION
    # --------------------------------------------------------

    allocation_fields = {
        "equity_percentage":
            product.equity_percentage,

        "debt_percentage":
            product.debt_percentage,

        "cash_percentage":
            product.cash_percentage,
    }

    for (
        field,
        value,
    ) in allocation_fields.items():

        if value is None:
            continue

        if (
            value < MIN_ALLOCATION
            or value > MAX_ALLOCATION
        ):
            issues.append(
                _issue(
                    code=(
                        "INVALID_ASSET_ALLOCATION"
                    ),
                    severity="CRITICAL",
                    message=(
                        f"{field} must be "
                        "between 0 and 100."
                    ),
                    product_id=product.id,
                    field=field,
                    value=value,
                )
            )

    available_allocations = [
        value
        for value
        in allocation_fields.values()
        if value is not None
    ]

    if (
        len(
            available_allocations
        )
        == 3
    ):

        allocation_total = sum(
            available_allocations
        )

        if (
            abs(
                allocation_total
                - 100.0
            )
            >
            ALLOCATION_TOTAL_TOLERANCE
        ):
            issues.append(
                _issue(
                    code=(
                        "ASSET_ALLOCATION_TOTAL"
                    ),
                    severity="WARNING",
                    message=(
                        "Equity + debt + cash "
                        "allocation does not "
                        "approximately equal 100%."
                    ),
                    product_id=product.id,
                    field=(
                        "asset_allocation"
                    ),
                    value=round(
                        allocation_total,
                        4,
                    ),
                )
            )

    # --------------------------------------------------------
    # MARKET CAP ALLOCATION
    # --------------------------------------------------------

    market_cap_fields = {
        "large_cap_percentage":
            product.large_cap_percentage,

        "mid_cap_percentage":
            product.mid_cap_percentage,

        "small_cap_percentage":
            product.small_cap_percentage,
    }

    for (
        field,
        value,
    ) in market_cap_fields.items():

        if value is None:
            continue

        if (
            value < MIN_ALLOCATION
            or value > MAX_ALLOCATION
        ):
            issues.append(
                _issue(
                    code=(
                        "INVALID_MARKET_CAP"
                    ),
                    severity="CRITICAL",
                    message=(
                        f"{field} must be "
                        "between 0 and 100."
                    ),
                    product_id=product.id,
                    field=field,
                    value=value,
                )
            )

    market_cap_values = [
        value
        for value
        in market_cap_fields.values()
        if value is not None
    ]

    if (
        len(
            market_cap_values
        )
        == 3
    ):

        market_cap_total = sum(
            market_cap_values
        )

        if (
            abs(
                market_cap_total
                - 100.0
            )
            >
            ALLOCATION_TOTAL_TOLERANCE
        ):
            issues.append(
                _issue(
                    code=(
                        "MARKET_CAP_TOTAL"
                    ),
                    severity="WARNING",
                    message=(
                        "Large + mid + small "
                        "cap allocation does not "
                        "approximately equal 100%."
                    ),
                    product_id=product.id,
                    field=(
                        "market_cap_allocation"
                    ),
                    value=round(
                        market_cap_total,
                        4,
                    ),
                )
            )

    # --------------------------------------------------------
    # DATE CONSISTENCY
    # --------------------------------------------------------

    if (
        product.launch_date
        is not None
        and product.nav_date
        is not None
        and product.launch_date
        > product.nav_date
    ):
        issues.append(
            _issue(
                code="INVALID_DATE_ORDER",
                severity="CRITICAL",
                message=(
                    "Launch date occurs after "
                    "the current NAV date."
                ),
                product_id=product.id,
            )
        )

    return issues


# ============================================================
# DATABASE VALIDATION
# ============================================================

def validate_fund_database(
    db: Session,
    *,
    batch_size: int = 500,
    max_issue_samples: int = 100,
) -> dict[str, Any]:

    total = (
        db.query(
            func.count(
                InvestmentProduct.id
            )
        )
        .filter(
            InvestmentProduct.is_active
            == True
        )
        .scalar()
        or 0
    )

    lifecycle_rows = (
        db.query(
            InvestmentProduct.scheme_status,
            func.count(InvestmentProduct.id),
        )
        .filter(
            InvestmentProduct.is_active
            == True
        )
        .group_by(
            InvestmentProduct.scheme_status
        )
        .all()
    )

    lifecycle_counts = {
        (status or "ACTIVE"): count
        for status, count
        in lifecycle_rows
    }

    checked = 0

    critical_count = 0
    warning_count = 0

    issue_counts: dict[
        str,
        int,
    ] = {}

    samples: list[
        dict[str, Any]
    ] = []

    last_id = 0

    while True:

        products = (
            db.query(
                InvestmentProduct
            )
            .filter(
                InvestmentProduct.is_active
                == True,

                InvestmentProduct.id
                > last_id,
            )
            .order_by(
                InvestmentProduct.id
            )
            .limit(
                batch_size
            )
            .all()
        )

        if not products:
            break

        for product in products:

            checked += 1

            issues = (
                validate_product_data(
                    product
                )
            )

            for issue in issues:

                code = issue[
                    "code"
                ]

                issue_counts[code] = (
                    issue_counts.get(
                        code,
                        0,
                    )
                    + 1
                )

                if (
                    issue["severity"]
                    == "CRITICAL"
                ):
                    critical_count += 1

                else:
                    warning_count += 1

                if (
                    len(samples)
                    < max_issue_samples
                ):
                    samples.append(
                        issue
                    )

            last_id = product.id

        db.expunge_all()

    status = "HEALTHY"

    if critical_count > 0:
        status = "CRITICAL"

    elif warning_count > 0:
        status = "WARNING"

    return {
        "status": status,

        "total_active_products":
            total,

        "products_checked":
            checked,

        "critical_issues":
            critical_count,

        "warnings":
            warning_count,

        "issue_counts":
            issue_counts,

        "lifecycle_counts":
            lifecycle_counts,

        "sample_issues":
            samples,

        "validation_coverage_pct":
            _percentage(
                checked,
                total,
            ),
    }
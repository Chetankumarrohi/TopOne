from bisect import bisect_right
from datetime import timedelta
from math import isfinite

from sqlalchemy.orm import Session

from app.investments.models.investment_product import (
    InvestmentProduct,
)

from app.investments.models.fund_nav_history import (
    FundNAVHistory,
)


# ============================================================
# CONFIGURATION
# ============================================================

# Target calendar-day horizons
RETURN_HORIZONS = {
    "1m": 30,
    "3m": 90,
    "6m": 180,
    "1y": 365,
    "3y": 1095,
    "5y": 1825,
}

# Maximum distance allowed between the desired historical
# date and the NAV observation we use.
#
# We only select NAVs ON OR BEFORE the target date.
# This prevents look-ahead bias.
HORIZON_TOLERANCE = {
    "1m": 10,
    "3m": 14,
    "6m": 21,
    "1y": 35,
    "3y": 60,
    "5y": 75,
}


# Maximum permitted absolute change between two consecutive
# NAV observations before we treat the series as having a
# structural discontinuity.
#
# This is intentionally conservative. It is designed to catch
# unit/NAV rebasing, IDCW-related resets, segregated-portfolio
# events, scheme restructuring and other non-economic jumps
# such as 100 -> 1000 or 12000 -> 120.
MAX_DAILY_NAV_JUMP_PCT = 50.0


# ============================================================
# HELPERS
# ============================================================

def safe_float(value):
    try:
        if value is None:
            return None

        result = float(value)

        if not isfinite(result):
            return None

        return result

    except (
        TypeError,
        ValueError,
    ):
        return None


def round_return(
    value,
):
    if value is None:
        return None

    return round(
        float(value),
        4,
    )


# ============================================================
# NAV DISCONTINUITY DETECTION
# ============================================================

def calculate_nav_change_pct(
    previous_nav,
    current_nav,
):
    """
    Percentage change between two consecutive NAV values.
    """

    previous_nav = safe_float(
        previous_nav
    )

    current_nav = safe_float(
        current_nav
    )

    if (
        previous_nav is None
        or current_nav is None
        or previous_nav <= 0
        or current_nav <= 0
    ):
        return None

    result = (
        (
            current_nav
            / previous_nav
        )
        - 1
    ) * 100

    if not isfinite(result):
        return None

    return result


def find_structural_breaks(
    history,
):
    """
    Detect extreme jumps between consecutive NAV observations.

    A returned index represents the CURRENT row where the
    discontinuity starts. For example, if history[25] jumps
    sharply relative to history[24], index 25 is stored.

    These breaks are used to reject horizon returns that span
    a likely unit/NAV rebasing or other non-economic event.
    """

    breaks = set()

    if len(history) < 2:
        return breaks

    for index in range(
        1,
        len(history),
    ):
        previous_nav = (
            history[index - 1][1]
        )

        current_nav = (
            history[index][1]
        )

        change_pct = (
            calculate_nav_change_pct(
                previous_nav,
                current_nav,
            )
        )

        if change_pct is None:
            continue

        if (
            abs(change_pct)
            > MAX_DAILY_NAV_JUMP_PCT
        ):
            breaks.add(
                index
            )

    return breaks


def horizon_crosses_structural_break(
    start_index: int,
    end_index: int,
    structural_breaks,
):
    """
    Return True if the requested return window crosses any
    detected structural NAV discontinuity.

    start_index is the historical observation used as the
    beginning of the return period. end_index is normally the
    latest NAV observation.
    """

    if (
        start_index < 0
        or end_index < 0
        or start_index >= end_index
    ):
        return False

    for break_index in structural_breaks:

        if (
            start_index
            < break_index
            <= end_index
        ):
            return True

    return False


# ============================================================
# NAV HISTORY
# ============================================================

def get_nav_history(
    db: Session,
    product_id: int,
):
    """
    Return compact NAV history:

        [
            (nav_date, nav),
            ...
        ]

    ordered oldest -> newest.

    Only the two required columns are loaded instead of full
    SQLAlchemy ORM objects.
    """

    rows = (
        db.query(
            FundNAVHistory.nav_date,
            FundNAVHistory.nav,
        )
        .filter(
            FundNAVHistory.product_id
            == product_id
        )
        .order_by(
            FundNAVHistory.nav_date.asc()
        )
        .all()
    )

    clean_rows = []

    for (
        nav_date,
        nav,
    ) in rows:

        nav_value = safe_float(
            nav
        )

        if (
            nav_date is None
            or nav_value is None
            or nav_value <= 0
        ):
            continue

        clean_rows.append(
            (
                nav_date,
                nav_value,
            )
        )

    return clean_rows


# ============================================================
# FIND HISTORICAL NAV
# ============================================================

def find_nav_on_or_before(
    history,
    target_date,
    tolerance_days: int,
):
    """
    Find the latest NAV on or before target_date.

    Example:

        target = Sunday
        available = Friday

    Friday NAV is used.

    We never use a date AFTER target_date because that would
    introduce look-ahead bias.

    Returns:

        (index, nav_date, nav)

    or:

        None

    Returning the index lets the caller determine whether the
    requested horizon crosses a structural NAV discontinuity.
    """

    if not history:
        return None

    dates = [
        row[0]
        for row in history
    ]

    index = (
        bisect_right(
            dates,
            target_date,
        )
        - 1
    )

    if index < 0:
        return None

    nav_date, nav = (
        history[index]
    )

    difference = (
        target_date
        - nav_date
    ).days

    if difference < 0:
        return None

    if (
        difference
        > tolerance_days
    ):
        return None

    return (
        index,
        nav_date,
        nav,
    )


# ============================================================
# SIMPLE RETURN
# ============================================================

def calculate_simple_return(
    latest_nav,
    historical_nav,
):
    if (
        latest_nav is None
        or historical_nav is None
        or historical_nav <= 0
    ):
        return None

    result = (
        (
            latest_nav
            / historical_nav
        )
        - 1
    ) * 100

    if not isfinite(result):
        return None

    return result


# ============================================================
# CAGR
# ============================================================

def calculate_cagr(
    latest_nav,
    historical_nav,
    start_date,
    end_date,
):
    """
    Annualized return using the ACTUAL elapsed time.

    CAGR =
        (ending / beginning) ^ (1 / years) - 1
    """

    if (
        latest_nav is None
        or historical_nav is None
        or historical_nav <= 0
        or latest_nav <= 0
    ):
        return None

    elapsed_days = (
        end_date
        - start_date
    ).days

    if elapsed_days <= 0:
        return None

    years = (
        elapsed_days
        / 365.25
    )

    if years <= 0:
        return None

    try:

        result = (
            (
                latest_nav
                / historical_nav
            )
            ** (
                1 / years
            )
            - 1
        ) * 100

        if not isfinite(
            result
        ):
            return None

        return result

    except (
        ValueError,
        OverflowError,
        ZeroDivisionError,
    ):
        return None


# ============================================================
# ONE PRODUCT RETURN ENGINE
# ============================================================

def calculate_product_returns(
    db: Session,
    product: InvestmentProduct,
):
    history = (
        get_nav_history(
            db=db,
            product_id=product.id,
        )
    )

    if not history:

        return {
            "product_id":
                product.id,

            "history_rows":
                0,

            "history_days":
                0,

            "returns": {},
        }

    first_date = (
        history[0][0]
    )

    latest_date = (
        history[-1][0]
    )

    latest_nav = (
        history[-1][1]
    )

    history_days = (
        latest_date
        - first_date
    ).days

    structural_breaks = (
        find_structural_breaks(
            history
        )
    )

    latest_index = (
        len(history)
        - 1
    )

    calculated = {}

    # ========================================================
    # 1 DAY RETURN
    # ========================================================

    if len(history) >= 2:

        # If the latest observation itself begins a detected
        # structural break, the one-period return is invalid.
        if (
            latest_index
            in structural_breaks
        ):

            calculated[
                "return_1d"
            ] = None

        else:

            previous_nav = (
                history[-2][1]
            )

            calculated[
                "return_1d"
            ] = round_return(
                calculate_simple_return(
                    latest_nav,
                    previous_nav,
                )
            )

    else:

        calculated[
            "return_1d"
        ] = None

    # ========================================================
    # TIME HORIZONS
    # ========================================================

    for (
        horizon,
        days,
    ) in RETURN_HORIZONS.items():

        target_date = (
            latest_date
            - timedelta(
                days=days
            )
        )

        historical = (
            find_nav_on_or_before(
                history=history,
                target_date=target_date,
                tolerance_days=(
                    HORIZON_TOLERANCE[
                        horizon
                    ]
                ),
            )
        )

        if historical is None:

            calculated[
                f"return_{horizon}"
            ] = None

            continue

        (
            historical_index,
            historical_date,
            historical_nav,
        ) = historical

        # Reject the horizon if any detected structural NAV
        # break lies between the historical observation and
        # the latest observation.
        if (
            horizon_crosses_structural_break(
                start_index=
                    historical_index,

                end_index=
                    latest_index,

                structural_breaks=
                    structural_breaks,
            )
        ):

            calculated[
                f"return_{horizon}"
            ] = None

            continue

        # -----------------------------------------------
        # 3Y and 5Y use CAGR
        # -----------------------------------------------

        if horizon in {
            "3y",
            "5y",
        }:

            value = calculate_cagr(
                latest_nav=
                    latest_nav,

                historical_nav=
                    historical_nav,

                start_date=
                    historical_date,

                end_date=
                    latest_date,
            )

        # -----------------------------------------------
        # 1M / 3M / 6M / 1Y use trailing return
        # -----------------------------------------------

        else:

            value = (
                calculate_simple_return(
                    latest_nav,
                    historical_nav,
                )
            )

        calculated[
            f"return_{horizon}"
        ] = round_return(
            value
        )

    # ========================================================
    # SAVE
    # ========================================================

    product.return_1d = (
        calculated[
            "return_1d"
        ]
    )

    product.return_1m = (
        calculated[
            "return_1m"
        ]
    )

    product.return_3m = (
        calculated[
            "return_3m"
        ]
    )

    product.return_6m = (
        calculated[
            "return_6m"
        ]
    )

    # These DB fields are currently NOT NULL.
    #
    # Therefore unavailable long-term returns remain 0.0.
    #
    # IMPORTANT:
    # ML/data-quality code must use horizon availability,
    # not "return != 0", to determine eligibility.

    product.return_1y = (
        calculated[
            "return_1y"
        ]
        if calculated[
            "return_1y"
        ] is not None
        else 0.0
    )

    product.return_3y = (
        calculated[
            "return_3y"
        ]
        if calculated[
            "return_3y"
        ] is not None
        else 0.0
    )

    product.return_5y = (
        calculated[
            "return_5y"
        ]
        if calculated[
            "return_5y"
        ] is not None
        else 0.0
    )

    return {
        "product_id":
            product.id,

        "name":
            product.name,

        "first_nav_date":
            first_date.isoformat(),

        "latest_nav_date":
            latest_date.isoformat(),

        "history_rows":
            len(history),

        "history_days":
            history_days,

        "structural_break_count":
            len(
                structural_breaks
            ),

        "returns":
            calculated,
    }

def calculate_fund_returns_for_products(
    db: Session,
    product_ids,
    batch_size: int = 100,
):
    """
    Recalculate returns only for selected active,
    AMFI-mapped investment products.

    Intended for incremental daily pipeline execution
    after NAV synchronization identifies which products
    actually changed.
    """

    if not product_ids:
        return {
            "requested_products": 0,
            "eligible_products": 0,
            "processed": 0,
            "errors": 0,
            "funds_with_1y": 0,
            "funds_with_3y": 0,
            "funds_with_5y": 0,
        }

    clean_ids = sorted(
        {
            int(product_id)
            for product_id in product_ids
            if product_id is not None
        }
    )

    requested = len(clean_ids)

    processed = 0
    errors = 0

    with_1y = 0
    with_3y = 0
    with_5y = 0

    eligible = (
        db.query(InvestmentProduct.id)
        .filter(
            InvestmentProduct.id.in_(clean_ids),
            InvestmentProduct.is_active == True,
            InvestmentProduct.scheme_code.isnot(None),
        )
        .count()
    )

    for offset in range(
        0,
        len(clean_ids),
        batch_size,
    ):
        batch_ids = clean_ids[
            offset:offset + batch_size
        ]

        products = (
            db.query(InvestmentProduct)
            .filter(
                InvestmentProduct.id.in_(batch_ids),
                InvestmentProduct.is_active == True,
                InvestmentProduct.scheme_code.isnot(None),
            )
            .order_by(
                InvestmentProduct.id.asc()
            )
            .all()
        )

        for product in products:
            product_id = product.id

            try:
                result = calculate_product_returns(
                    db=db,
                    product=product,
                )

                returns = result["returns"]

                if returns.get("return_1y") is not None:
                    with_1y += 1

                if returns.get("return_3y") is not None:
                    with_3y += 1

                if returns.get("return_5y") is not None:
                    with_5y += 1

                processed += 1

            except Exception as exc:
                errors += 1

                print(
                    "Incremental return calculation "
                    f"failed for product "
                    f"{product_id}: {exc}"
                )

                db.rollback()

        db.commit()
        db.expunge_all()

    return {
        "requested_products": requested,
        "eligible_products": eligible,
        "processed": processed,
        "errors": errors,
        "funds_with_1y": with_1y,
        "funds_with_3y": with_3y,
        "funds_with_5y": with_5y,
    }


# ============================================================
# CALCULATE ALL PRODUCT RETURNS
# ============================================================

def calculate_all_fund_returns(
    db: Session,
    batch_size: int = 100,
):
    """
    Calculate returns across all active AMFI-mapped funds.

    Uses ID-based batching so the entire investment-product
    table does not remain in SQLAlchemy's identity map.
    """

    total = (
        db.query(
            InvestmentProduct
        )
        .filter(
            InvestmentProduct.is_active
            == True,

            InvestmentProduct.scheme_code
            .isnot(None),
        )
        .count()
    )

    processed = 0

    errors = 0

    with_1y = 0

    with_3y = 0

    with_5y = 0

    last_id = 0

    print(
        "\n"
        "============================================"
    )

    print(
        "TopOne Return Intelligence Engine"
    )

    print(
        "============================================"
    )

    print(
        f"Products to process: "
        f"{total:,}"
    )

    while True:

        products = (
            db.query(
                InvestmentProduct
            )
            .filter(
                InvestmentProduct.is_active
                == True,

                InvestmentProduct.scheme_code
                .isnot(None),

                InvestmentProduct.id
                > last_id,
            )
            .order_by(
                InvestmentProduct.id.asc()
            )
            .limit(
                batch_size
            )
            .all()
        )

        if not products:
            break

        for product in products:

            product_id = (
                product.id
            )

            try:

                result = (
                    calculate_product_returns(
                        db=db,
                        product=product,
                    )
                )

                returns = (
                    result["returns"]
                )

                if (
                    returns.get(
                        "return_1y"
                    )
                    is not None
                ):
                    with_1y += 1

                if (
                    returns.get(
                        "return_3y"
                    )
                    is not None
                ):
                    with_3y += 1

                if (
                    returns.get(
                        "return_5y"
                    )
                    is not None
                ):
                    with_5y += 1

                processed += 1

            except Exception as exc:

                errors += 1

                print(
                    f"\nReturn calculation "
                    f"error for product "
                    f"{product_id}: "
                    f"{exc}"
                )

                db.rollback()

            finally:

                last_id = (
                    product_id
                )

        db.commit()

        db.expunge_all()

        print(
            f"Return progress: "
            f"{processed:,}/"
            f"{total:,}"
            f" | 1Y={with_1y:,}"
            f" | 3Y={with_3y:,}"
            f" | 5Y={with_5y:,}"
            f" | errors={errors}"
        )

    result = {
        "total_products":
            total,

        "processed":
            processed,

        "errors":
            errors,

        "funds_with_1y":
            with_1y,

        "funds_with_3y":
            with_3y,

        "funds_with_5y":
            with_5y,
    }

    print(
        "\n"
        "============================================"
    )

    print(
        "Return Intelligence complete"
    )

    print(
        "============================================"
    )

    print(
        result
    )

    return result
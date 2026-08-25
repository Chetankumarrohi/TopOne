from datetime import date, datetime, timedelta
from math import sqrt

from sqlalchemy.orm import Session

from app.investments.models.investment_product import (
    InvestmentProduct,
)

from app.investments.models.fund_nav_history import (
    FundNAVHistory,
)


TRADING_DAYS_PER_YEAR = 252


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def percentage_return(
    old_value: float,
    new_value: float,
):
    if not old_value or old_value <= 0:
        return None

    return (
        (new_value - old_value)
        / old_value
    ) * 100


def find_nav_near_date(
    history: list[FundNAVHistory],
    target_date: date,
):
    """
    Returns the closest NAV on or before
    the requested target date.
    """

    eligible = [
        row
        for row in history
        if row.nav_date <= target_date
    ]

    if not eligible:
        return None

    return eligible[-1]


def calculate_period_return(
    history: list[FundNAVHistory],
    days: int,
):
    if len(history) < 2:
        return None

    latest = history[-1]

    target_date = (
        latest.nav_date
        - timedelta(days=days)
    )

    old_row = find_nav_near_date(
        history=history,
        target_date=target_date,
    )

    if not old_row:
        return None

    return percentage_return(
        old_value=old_row.nav,
        new_value=latest.nav,
    )


# ---------------------------------------------------------
# DAILY RETURNS
# ---------------------------------------------------------

def calculate_daily_returns(
    history: list[FundNAVHistory],
):
    returns = []

    for index in range(
        1,
        len(history),
    ):
        previous_nav = (
            history[index - 1].nav
        )

        current_nav = (
            history[index].nav
        )

        if (
            previous_nav is None
            or previous_nav <= 0
        ):
            continue

        daily_return = (
            current_nav
            - previous_nav
        ) / previous_nav

        returns.append(
            daily_return
        )

    return returns


# ---------------------------------------------------------
# STANDARD DEVIATION
# ---------------------------------------------------------

def calculate_standard_deviation(
    values: list[float],
):
    if len(values) < 2:
        return None

    average = (
        sum(values)
        / len(values)
    )

    variance = (
        sum(
            (
                value
                - average
            ) ** 2
            for value in values
        )
        / (
            len(values)
            - 1
        )
    )

    return sqrt(
        variance
    )


# ---------------------------------------------------------
# ANNUALISED VOLATILITY
# ---------------------------------------------------------

def calculate_volatility(
    daily_returns: list[float],
):
    standard_deviation = (
        calculate_standard_deviation(
            daily_returns
        )
    )

    if standard_deviation is None:
        return None

    annualised = (
        standard_deviation
        * sqrt(
            TRADING_DAYS_PER_YEAR
        )
        * 100
    )

    return annualised


# ---------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------

def calculate_sharpe_ratio(
    daily_returns: list[float],
    risk_free_rate: float = 0.07,
):
    """
    risk_free_rate:
    annual decimal rate.

    Example:
    7% = 0.07
    """

    if len(daily_returns) < 2:
        return None

    mean_daily_return = (
        sum(daily_returns)
        / len(daily_returns)
    )

    daily_std = (
        calculate_standard_deviation(
            daily_returns
        )
    )

    if (
        daily_std is None
        or daily_std == 0
    ):
        return None

    daily_risk_free = (
        risk_free_rate
        / TRADING_DAYS_PER_YEAR
    )

    sharpe = (
        (
            mean_daily_return
            - daily_risk_free
        )
        / daily_std
    ) * sqrt(
        TRADING_DAYS_PER_YEAR
    )

    return sharpe


# ---------------------------------------------------------
# MAXIMUM DRAWDOWN
# ---------------------------------------------------------

def calculate_max_drawdown(
    history: list[FundNAVHistory],
):
    if not history:
        return None

    peak = history[0].nav

    max_drawdown = 0

    for row in history:
        nav = row.nav

        if nav > peak:
            peak = nav

        if peak <= 0:
            continue

        drawdown = (
            (nav - peak)
            / peak
        ) * 100

        if drawdown < max_drawdown:
            max_drawdown = (
                drawdown
            )

    return max_drawdown


# ---------------------------------------------------------
# CAGR
# ---------------------------------------------------------

def calculate_cagr(
    history: list[FundNAVHistory],
):
    if len(history) < 2:
        return None

    first = history[0]
    last = history[-1]

    if (
        first.nav <= 0
        or last.nav <= 0
    ):
        return None

    days = (
        last.nav_date
        - first.nav_date
    ).days

    if days <= 0:
        return None

    years = (
        days / 365.25
    )

    if years <= 0:
        return None

    cagr = (
        (
            last.nav
            / first.nav
        )
        ** (
            1 / years
        )
        - 1
    ) * 100

    return cagr


# ---------------------------------------------------------
# PERFORMANCE SCORE
# ---------------------------------------------------------

def calculate_performance_score(
    return_1y: float | None,
    volatility: float | None,
    sharpe_ratio: float | None,
):
    """
    Development-stage fund performance score.

    This is NOT the personalized AI Fit Score.

    AI Fit Score will later combine:
    - risk profile
    - Wealth DNA
    - goals
    - portfolio
    - ML prediction
    - news sentiment
    """

    score = 50.0

    if return_1y is not None:
        if return_1y >= 20:
            score += 20

        elif return_1y >= 12:
            score += 15

        elif return_1y >= 8:
            score += 8

        elif return_1y < 0:
            score -= 15

    if sharpe_ratio is not None:
        if sharpe_ratio >= 1.5:
            score += 15

        elif sharpe_ratio >= 1:
            score += 10

        elif sharpe_ratio >= 0.5:
            score += 5

        elif sharpe_ratio < 0:
            score -= 10

    if volatility is not None:
        if volatility <= 10:
            score += 10

        elif volatility >= 25:
            score -= 10

    return round(
        max(
            0,
            min(
                100,
                score,
            ),
        ),
        2,
    )


# ---------------------------------------------------------
# ANALYSE ONE FUND
# ---------------------------------------------------------

def calculate_fund_analytics(
    db: Session,
    product: InvestmentProduct,
):
    history = (
        db.query(
            FundNAVHistory
        )
        .filter(
            FundNAVHistory.product_id
            == product.id
        )
        .order_by(
            FundNAVHistory.nav_date.asc()
        )
        .all()
    )

    if len(history) < 2:
        return {
            "product_id":
                product.id,

            "scheme_code":
                product.scheme_code,

            "name":
                product.name,

            "status":
                "INSUFFICIENT_HISTORY",
        }

    daily_returns = (
        calculate_daily_returns(
            history
        )
    )

    return_1d = (
        percentage_return(
            history[-2].nav,
            history[-1].nav,
        )
    )

    return_1m = (
        calculate_period_return(
            history,
            30,
        )
    )

    return_3m = (
        calculate_period_return(
            history,
            90,
        )
    )

    return_6m = (
        calculate_period_return(
            history,
            180,
        )
    )

    return_1y = (
        calculate_period_return(
            history,
            365,
        )
    )

    return_3y = (
        calculate_period_return(
            history,
            365 * 3,
        )
    )

    return_5y = (
        calculate_period_return(
            history,
            365 * 5,
        )
    )

    volatility = (
        calculate_volatility(
            daily_returns
        )
    )

    daily_std = (
        calculate_standard_deviation(
            daily_returns
        )
    )

    sharpe_ratio = (
        calculate_sharpe_ratio(
            daily_returns
        )
    )

    max_drawdown = (
        calculate_max_drawdown(
            history
        )
    )

    cagr = (
        calculate_cagr(
            history
        )
    )

    performance_score = (
        calculate_performance_score(
            return_1y=
                return_1y,

            volatility=
                volatility,

            sharpe_ratio=
                sharpe_ratio,
        )
    )

    return {
        "product_id":
            product.id,

        "scheme_code":
            product.scheme_code,

        "name":
            product.name,

        "nav":
            history[-1].nav,

        "nav_date":
            history[-1].nav_date,

        "history_points":
            len(history),

        "return_1d":
            round_optional(
                return_1d
            ),

        "return_1m":
            round_optional(
                return_1m
            ),

        "return_3m":
            round_optional(
                return_3m
            ),

        "return_6m":
            round_optional(
                return_6m
            ),

        "return_1y":
            round_optional(
                return_1y
            ),

        "return_3y":
            round_optional(
                return_3y
            ),

        "return_5y":
            round_optional(
                return_5y
            ),

        "volatility":
            round_optional(
                volatility
            ),

        "standard_deviation":
            round_optional(
                (
                    daily_std * 100
                    if daily_std
                    is not None
                    else None
                )
            ),

        "sharpe_ratio":
            round_optional(
                sharpe_ratio
            ),

        "max_drawdown":
            round_optional(
                max_drawdown
            ),

        "cagr":
            round_optional(
                cagr
            ),

        "performance_score":
            performance_score,

        "calculated_at":
            datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------
# UPDATE STORED ANALYTICS
# ---------------------------------------------------------

def update_product_analytics(
    db: Session,
    product: InvestmentProduct,
):
    analytics = (
        calculate_fund_analytics(
            db=db,
            product=product,
        )
    )

    if (
        analytics.get("status")
        == "INSUFFICIENT_HISTORY"
    ):
        return analytics

    product.return_1d = (
        analytics["return_1d"]
    )

    product.return_1m = (
        analytics["return_1m"]
    )

    product.return_3m = (
        analytics["return_3m"]
    )

    product.return_6m = (
        analytics["return_6m"]
    )

    if (
        analytics["return_1y"]
        is not None
    ):
        product.return_1y = (
            analytics["return_1y"]
        )

    if (
        analytics["return_3y"]
        is not None
    ):
        product.return_3y = (
            analytics["return_3y"]
        )

    if (
        analytics["return_5y"]
        is not None
    ):
        product.return_5y = (
            analytics["return_5y"]
        )

    if (
        analytics["volatility"]
        is not None
    ):
        product.volatility = (
            analytics["volatility"]
        )

    product.standard_deviation = (
        analytics[
            "standard_deviation"
        ]
    )

    product.sharpe_ratio = (
        analytics[
            "sharpe_ratio"
        ]
    )

    return analytics


# ---------------------------------------------------------
# UTILITY
# ---------------------------------------------------------

def round_optional(
    value,
    digits: int = 4,
):
    if value is None:
        return None

    return round(
        float(value),
        digits,
    )
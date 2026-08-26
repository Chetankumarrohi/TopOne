from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timedelta
from math import sqrt, log10
from statistics import mean, stdev
import re

from sqlalchemy.orm import Session

from app.investments.models.investment_product import InvestmentProduct
from app.investments.models.fund_nav_history import FundNAVHistory
from app.investments.models.fund_health_history import FundHealthHistory


# ============================================================
# CONFIGURATION
# ============================================================

MIN_HISTORY_DAYS = 30
MIN_LONG_TERM_DAYS = 180


STATUS_THRESHOLDS = {
    # Provisional absolute-score thresholds used while one fund is
    # calculated. The final Fund Radar status is assigned in the
    # category-relative peer pass.
    "IN_FORM": 85,
    "ON_TRACK": 70,
    "OFF_TRACK": 50,
}

MIN_PEER_GROUP_SIZE = 8

FORM_THRESHOLDS = {
    "IN_FORM": 80.0,
    "ON_TRACK": 50.0,
    "OFF_TRACK": 20.0,
}

FORM_WEIGHTS = {
    "long_term": 0.25,
    "consistency": 0.20,
    "risk_adjusted": 0.15,
    "momentum": 0.15,
    "downside": 0.10,
    "volatility": 0.10,
    "quality": 0.05,
}


# ============================================================
# FINAL FUND HEALTH WEIGHTS
# ============================================================
#
# Total = 100%
#
# Historical / quantitative intelligence = 90%
# News intelligence                     = 10%
#
# News is intentionally separated so the
# real News Intelligence Engine can be
# connected later without changing the
# rest of the scoring architecture.
#
# ============================================================

WEIGHTS = {
    "long_term": 0.15,
    "consistency": 0.12,
    "risk_adjusted": 0.12,
    "downside": 0.10,
    "volatility": 0.08,
    "momentum": 0.08,
    "peer": 0.10,
    "quality": 0.08,
    "fundamental": 0.07,
    "news": 0.10,
}


# ============================================================
# BASIC HELPERS
# ============================================================

def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
):
    """
    Keep a score between minimum and maximum.
    """

    return max(
        minimum,
        min(maximum, value),
    )


def safe_float(value):
    """
    Safely convert a value to float.
    """

    try:

        if value is None:
            return None

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return None


# ============================================================
# PEER PERCENTILE HELPERS
# ============================================================

def percentile_score(
    value,
    values,
):
    """
    Convert a raw value into a 0-100 peer percentile.

    Higher value = better score.
    """

    if value is None or not values:
        return None

    clean_values = [
        float(v)
        for v in values
        if v is not None
    ]

    if not clean_values:
        return None

    below_or_equal = sum(
        1
        for v in clean_values
        if v <= value
    )

    return clamp(
        (
            below_or_equal
            / len(clean_values)
        )
        * 100
    )


def inverse_percentile_score(
    value,
    values,
):
    """
    Convert a raw value into a 0-100 percentile
    where lower values are better.

    Used for:
    - volatility
    - drawdown
    - other downside metrics
    """

    if value is None or not values:
        return None

    clean_values = [
        float(v)
        for v in values
        if v is not None
    ]

    if not clean_values:
        return None

    below_or_equal = sum(
        1
        for v in clean_values
        if v <= value
    )

    return clamp(
        100
        - (
            (
                below_or_equal
                / len(clean_values)
            )
            * 100
        )
    )


# ============================================================
# NAV HISTORY
# ============================================================

def get_nav_history(
    db: Session,
    product_id: int,
):
    """
    Fetch NAV history for a fund in chronological order.
    """

    return (
        db.query(FundNAVHistory)
        .filter(
            FundNAVHistory.product_id
            == product_id
        )
        .order_by(
            FundNAVHistory.nav_date.asc()
        )
        .all()
    )


# ============================================================
# RETURN CALCULATIONS
# ============================================================

def calculate_period_return(
    rows,
    days,
):
    """
    Calculate approximate absolute return over
    the requested period.

    Example:
        90 days
        365 days
    """

    if not rows:
        return None

    latest = rows[-1]

    target_date = (
        latest.nav_date
        - timedelta(days=days)
    )

    previous = None

    for row in rows:

        if row.nav_date <= target_date:
            previous = row

    if not previous:
        return None

    previous_nav = safe_float(
        previous.nav
    )

    latest_nav = safe_float(
        latest.nav
    )

    if (
        previous_nav is None
        or latest_nav is None
        or previous_nav <= 0
    ):
        return None

    return (
        (
            latest_nav
            / previous_nav
        )
        - 1
    ) * 100


def calculate_annualized_return(
    rows,
    days,
):
    """
    Calculate annualized return using NAV history.
    """

    if not rows:
        return None

    latest = rows[-1]

    target_date = (
        latest.nav_date
        - timedelta(days=days)
    )

    previous = None

    for row in rows:

        if row.nav_date <= target_date:
            previous = row

    if not previous:
        return None

    previous_nav = safe_float(
        previous.nav
    )

    latest_nav = safe_float(
        latest.nav
    )

    if (
        previous_nav is None
        or latest_nav is None
        or previous_nav <= 0
        or latest_nav <= 0
    ):
        return None

    actual_days = (
        latest.nav_date
        - previous.nav_date
    ).days

    if actual_days <= 0:
        return None

    years = (
        actual_days
        / 365.25
    )

    if years <= 0:
        return None

    return (
        (
            (
                latest_nav
                / previous_nav
            )
            ** (
                1 / years
            )
        )
        - 1
    ) * 100


# ============================================================
# DAILY RETURNS
# ============================================================

def calculate_daily_returns(rows):
    """
    Calculate daily percentage returns from NAV history.
    """

    returns = []

    previous_nav = None

    for row in rows:

        nav = safe_float(
            row.nav
        )

        if (
            nav is None
            or nav <= 0
        ):
            continue

        if (
            previous_nav is not None
            and previous_nav > 0
        ):

            daily_return = (
                (
                    nav
                    / previous_nav
                )
                - 1
            ) * 100

            returns.append(
                daily_return
            )

        previous_nav = nav

    return returns


# ============================================================
# VOLATILITY
# ============================================================

def calculate_volatility(
    daily_returns,
):
    """
    Annualized volatility based on daily returns.
    """

    if len(daily_returns) < 2:
        return None

    try:

        daily_std = stdev(
            daily_returns
        )

        return (
            daily_std
            * sqrt(252)
        )

    except Exception:

        return None


# ============================================================
# SHARPE RATIO
# ============================================================

def calculate_sharpe(
    daily_returns,
):
    """
    Approximate annualized Sharpe ratio.

    A zero risk-free rate is currently used.
    This can later be replaced with a dynamic
    risk-free rate.
    """

    if len(daily_returns) < 30:
        return None

    try:

        average_daily = mean(
            daily_returns
        )

        daily_std = stdev(
            daily_returns
        )

        if daily_std <= 0:
            return None

        return (
            average_daily
            / daily_std
        ) * sqrt(252)

    except Exception:

        return None


# ============================================================
# MAXIMUM DRAWDOWN
# ============================================================

def calculate_max_drawdown(
    rows,
):
    """
    Calculate maximum historical drawdown.
    """

    if not rows:
        return None

    peak = None
    max_drawdown = 0.0

    for row in rows:

        nav = safe_float(
            row.nav
        )

        if (
            nav is None
            or nav <= 0
        ):
            continue

        if peak is None:

            peak = nav

            continue

        if nav > peak:

            peak = nav

        drawdown = (
            (
                nav
                - peak
            )
            / peak
        ) * 100

        if drawdown < max_drawdown:

            max_drawdown = drawdown

    return abs(
        max_drawdown
    )


# ============================================================
# CONSISTENCY
# ============================================================

def calculate_consistency(
    daily_returns,
):
    """
    Measure consistency of positive daily returns.

    This is only one component of Fund Health.
    """

    if len(daily_returns) < 30:
        return None

    positive_days = sum(
        1
        for value in daily_returns
        if value > 0
    )

    positive_ratio = (
        positive_days
        / len(daily_returns)
    )

    return clamp(
        positive_ratio * 100
    )


# ============================================================
# MOMENTUM
# ============================================================

def calculate_momentum(
    rows,
):
    """
    Compare recent performance with
    longer-term performance.

    Uses:
        90-day return
        365-day return
    """

    short_return = (
        calculate_period_return(
            rows,
            90,
        )
    )

    medium_return = (
        calculate_period_return(
            rows,
            365,
        )
    )

    if (
        short_return is None
        or medium_return is None
    ):
        return None

    difference = (
        short_return
        - medium_return
    )

    score = (
        50
        + (
            difference
            * 3
        )
    )

    return clamp(
        score
    )


# ============================================================
# LONG-TERM SCORE
# ============================================================

def calculate_long_term_score(
    return_1y,
    return_3y,
    return_5y,
):
    """
    Long-term performance score.

    Uses available 1Y / 3Y / 5Y returns.
    """

    values = [
        value
        for value in [
            return_1y,
            return_3y,
            return_5y,
        ]
        if value is not None
    ]

    if not values:
        return None

    average_return = mean(
        values
    )

    score = (
        50
        + (
            average_return
            * 2.5
        )
    )

    return clamp(
        score
    )


# ============================================================
# RISK-ADJUSTED SCORE
# ============================================================

def calculate_risk_adjusted_score(
    sharpe,
    alpha,
):
    """
    Combine Sharpe ratio and alpha.

    Higher risk-adjusted performance
    receives a higher score.
    """

    scores = []

    if sharpe is not None:

        sharpe_score = (
            50
            + (
                sharpe
                * 25
            )
        )

        scores.append(
            clamp(
                sharpe_score
            )
        )

    if alpha is not None:

        alpha_score = (
            50
            + (
                alpha
                * 5
            )
        )

        scores.append(
            clamp(
                alpha_score
            )
        )

    if not scores:
        return None

    return mean(
        scores
    )


# ============================================================
# DOWNSIDE SCORE
# ============================================================

def calculate_downside_score(
    max_drawdown,
):
    """
    Lower maximum drawdown = better score.
    """

    if max_drawdown is None:
        return None

    score = (
        100
        - (
            max_drawdown
            * 3
        )
    )

    return clamp(
        score
    )


# ============================================================
# VOLATILITY SCORE
# ============================================================

def calculate_volatility_score(
    volatility,
):
    """
    Lower volatility = better score.
    """

    if volatility is None:
        return None

    score = (
        100
        - (
            volatility
            * 3
        )
    )

    return clamp(
        score
    )


# ============================================================
# FUND QUALITY
# ============================================================

def calculate_quality_score(
    expense_ratio,
    aum,
):
    """
    Estimate operational / structural quality.

    Current inputs:
        - expense ratio
        - AUM

    This should NOT dominate the Fund Health score.
    """

    scores = []

    if expense_ratio is not None:

        expense_score = (
            100
            - (
                expense_ratio
                * 20
            )
        )

        scores.append(
            clamp(
                expense_score
            )
        )

    if (
        aum is not None
        and aum > 0
    ):

        aum_score = (
            log10(
                max(
                    aum,
                    1,
                )
            )
            * 10
        )

        scores.append(
            clamp(
                aum_score
            )
        )

    if not scores:
        return None

    return mean(
        scores
    )


# ============================================================
# FUNDAMENTAL / PORTFOLIO SCORE
# ============================================================

def calculate_fundamental_score(
    equity_percentage,
    debt_percentage,
    cash_percentage,
    large_cap_percentage,
    mid_cap_percentage,
    small_cap_percentage,
):
    """
    Evaluate availability/completeness of portfolio
    composition information.

    IMPORTANT:
    This is currently a data-quality-oriented
    fundamental score.

    Later this can be upgraded to include:
        - concentration
        - sector concentration
        - market-cap concentration
        - credit quality
        - duration
        - portfolio turnover
        - portfolio quality
    """

    values = [
        equity_percentage,
        debt_percentage,
        cash_percentage,
        large_cap_percentage,
        mid_cap_percentage,
        small_cap_percentage,
    ]

    available = [
        value
        for value in values
        if value is not None
    ]

    if not available:
        return None

    completeness = (
        len(available)
        / len(values)
    ) * 100

    return clamp(
        completeness
    )


# ============================================================
# NEWS SCORE
# ============================================================

def calculate_news_score(
    product=None,
):
    """
    TEMPORARY NEWS INTELLIGENCE SCORE.

    Current implementation:
        Neutral score = 50.

    This function is deliberately isolated.

    NEXT PHASE:
        Replace this with the actual Daily News
        Intelligence Engine.

    The future engine will consider things such as:

        - fund house news
        - AMC regulatory news
        - SEBI actions
        - manager changes
        - fund strategy changes
        - major portfolio events
        - major holdings news
        - sector-specific news
        - credit events
        - rating changes
        - market/regulatory events
        - negative sentiment
        - positive sentiment
        - news recency
        - source reliability
        - event severity
        - repeated negative coverage

    Output must remain:
        0 - 100

    50 = neutral
    >50 = positive
    <50 = negative
    """

    return 50.0


# ============================================================
# DATA QUALITY
# ============================================================

def calculate_data_quality(
    rows,
):
    """
    Determine reliability based on available
    historical NAV observations.
    """

    if not rows:
        return 0.0

    days = len(rows)

    if days < MIN_HISTORY_DAYS:
        return 20.0

    if days < 90:
        return 45.0

    if days < 180:
        return 65.0

    if days < 365:
        return 80.0

    if days < 730:
        return 90.0

    return 100.0


# ============================================================
# STATUS CLASSIFICATION
# ============================================================

def classify_status(
    score,
    data_quality,
    history_days,
):
    """
    Convert Fund Health Score into one of:

        IN_FORM
        ON_TRACK
        OFF_TRACK
        NOT_IN_FORM
        UNRATED
    """

    if (
        score is None
        or history_days < MIN_HISTORY_DAYS
        or data_quality < 40
    ):

        return "UNRATED"

    if (
        score
        >= STATUS_THRESHOLDS[
            "IN_FORM"
        ]
    ):

        return "IN_FORM"

    if (
        score
        >= STATUS_THRESHOLDS[
            "ON_TRACK"
        ]
    ):

        return "ON_TRACK"

    if (
        score
        >= STATUS_THRESHOLDS[
            "OFF_TRACK"
        ]
    ):

        return "OFF_TRACK"

    return "NOT_IN_FORM"


# ============================================================
# HEALTH SUMMARY
# ============================================================

def generate_health_summary(
    status,
    score,
    momentum,
    volatility,
    max_drawdown,
):
    """
    Generate a concise explanation for the UI.
    """

    if status == "UNRATED":

        return (
            "Insufficient historical data is "
            "available to reliably assess this fund."
        )

    parts = [
        (
            "TopOne Fund Health Score: "
            f"{round(score, 1)}/100."
        )
    ]

    if status == "IN_FORM":

        parts.append(
            "The fund currently shows strong "
            "overall health across performance, "
            "consistency and risk characteristics."
        )

    elif status == "ON_TRACK":

        parts.append(
            "The fund is performing within a "
            "healthy range, although some metrics "
            "may not be among the strongest in "
            "its peer group."
        )

    elif status == "OFF_TRACK":

        parts.append(
            "Recent or risk-related indicators "
            "suggest that the fund requires "
            "closer monitoring."
        )

    elif status == "NOT_IN_FORM":

        parts.append(
            "The fund currently shows materially "
            "weaker health characteristics and "
            "should be reviewed carefully."
        )

    if momentum is not None:

        if momentum >= 65:

            parts.append(
                "Recent momentum is positive."
            )

        elif momentum <= 35:

            parts.append(
                "Recent momentum is weak."
            )

    if volatility is not None:

        parts.append(
            "Observed annualized volatility is "
            f"approximately "
            f"{round(volatility, 2)}%."
        )

    if max_drawdown is not None:

        parts.append(
            "Maximum observed drawdown is "
            f"approximately "
            f"{round(max_drawdown, 2)}%."
        )

    return " ".join(
        parts
    )


# ============================================================
# CATEGORY-RELATIVE FUND FORM ENGINE
# ============================================================

def _fund_text(product):
    return " ".join(
        str(value)
        for value in [
            getattr(product, "category", None),
            getattr(product, "sub_category", None),
            getattr(product, "asset_class", None),
            getattr(product, "name", None),
        ]
        if value
    ).lower().replace("âs", "'s").replace("&", " and ")


def get_peer_family(product):
    text = _fund_text(product)

    if any(x in text for x in [
        "equity scheme", "large cap", "mid cap", "small cap",
        "flexi cap", "multi cap", "elss", "focused fund",
        "value fund", "dividend yield", "sectoral", "thematic",
    ]):
        return "EQUITY"

    if any(x in text for x in [
        "debt scheme", "income/debt", "liquid fund", "overnight fund",
        "duration fund", "money market", "corporate bond", "credit risk",
        "banking and psu", "gilt fund", "floater fund", "dynamic bond",
    ]):
        return "DEBT"

    if any(x in text for x in [
        "hybrid scheme", "aggressive hybrid", "conservative hybrid",
        "balanced advantage", "dynamic asset allocation", "arbitrage",
        "equity savings", "multi asset",
    ]):
        return "HYBRID"

    if any(x in text for x in [
        "index fund", "index funds", "etf", "exchange traded", "gold",
    ]):
        return "INDEX_ETF"

    if "fof" in text or "fund of funds" in text:
        return "FOF"

    return "OTHER"


def get_peer_group(product):
    text = _fund_text(product)
    family = get_peer_family(product)

    if family == "EQUITY":
        if "large and mid cap" in text or "large & mid cap" in text:
            return "EQUITY:LARGE_MID"
        if "large cap" in text:
            return "EQUITY:LARGE"
        if "mid cap" in text:
            return "EQUITY:MID"
        if "small cap" in text:
            return "EQUITY:SMALL"
        if "flexi cap" in text:
            return "EQUITY:FLEXI"
        if "multi cap" in text:
            return "EQUITY:MULTI"
        if "elss" in text:
            return "EQUITY:ELSS"
        if "focused fund" in text:
            return "EQUITY:FOCUSED"
        if "dividend yield" in text:
            return "EQUITY:DIVIDEND_YIELD"
        if "value fund" in text:
            return "EQUITY:VALUE"
        if "sectoral" in text or "thematic" in text:
            return "EQUITY:SECTORAL_THEMATIC"
        return "EQUITY:OTHER"

    if family == "DEBT":
        checks = [
            ("overnight", "DEBT:OVERNIGHT"),
            ("liquid", "DEBT:LIQUID"),
            ("ultra short", "DEBT:ULTRA_SHORT"),
            ("low duration", "DEBT:LOW_DURATION"),
            ("money market", "DEBT:MONEY_MARKET"),
            ("medium to long", "DEBT:MEDIUM_LONG"),
            ("medium duration", "DEBT:MEDIUM"),
            ("short duration", "DEBT:SHORT"),
            ("long duration", "DEBT:LONG"),
            ("dynamic bond", "DEBT:DYNAMIC_BOND"),
            ("corporate bond", "DEBT:CORPORATE_BOND"),
            ("credit risk", "DEBT:CREDIT_RISK"),
            ("banking and psu", "DEBT:BANKING_PSU"),
            ("floater", "DEBT:FLOATER"),
            ("10 year constant", "DEBT:GILT_10Y"),
            ("gilt", "DEBT:GILT"),
        ]
        for token, group in checks:
            if token in text:
                return group
        return "DEBT:OTHER"

    if family == "HYBRID":
        checks = [
            ("aggressive hybrid", "HYBRID:AGGRESSIVE"),
            ("conservative hybrid", "HYBRID:CONSERVATIVE"),
            ("balanced advantage", "HYBRID:BALANCED_ADVANTAGE"),
            ("dynamic asset allocation", "HYBRID:BALANCED_ADVANTAGE"),
            ("arbitrage", "HYBRID:ARBITRAGE"),
            ("equity savings", "HYBRID:EQUITY_SAVINGS"),
            ("multi asset", "HYBRID:MULTI_ASSET"),
        ]
        for token, group in checks:
            if token in text:
                return group
        return "HYBRID:OTHER"

    if family == "INDEX_ETF":
        if "gold" in text:
            return "INDEX_ETF:GOLD"
        if "etf" in text or "exchange traded" in text:
            return "INDEX_ETF:ETF"
        if "index" in text:
            return "INDEX_ETF:INDEX"
        return "INDEX_ETF:OTHER"

    if family == "FOF":
        if "overseas" in text:
            return "FOF:OVERSEAS"
        if "domestic" in text:
            return "FOF:DOMESTIC"
        return "FOF:OTHER"

    if "close ended" in text:
        return "OTHER:CLOSE_ENDED"
    if "interval" in text:
        return "OTHER:INTERVAL"
    if "retirement" in text:
        return "OTHER:RETIREMENT"
    if "children" in text:
        return "OTHER:CHILDREN"

    return "OTHER:GENERAL"


def _sorted_values(values):
    return sorted(
        float(value)
        for value in values
        if value is not None
    )


def _percentile(value, sorted_values):
    if value is None or not sorted_values:
        return None

    return clamp(
        (
            bisect_right(
                sorted_values,
                float(value),
            )
            / len(sorted_values)
        )
        * 100
    )


def _quality_for_peer(row):
    return calculate_quality_score(
        safe_float(row.expense_ratio),
        safe_float(row.aum),
    )


def calculate_peer_form_score(
    row,
    distributions,
):
    raw = {
        "long_term": safe_float(row.long_term_score),
        "consistency": safe_float(row.consistency_score),
        "risk_adjusted": safe_float(row.risk_adjusted_score),
        "momentum": safe_float(row.momentum_score),
        "downside": safe_float(row.downside_score),
        "volatility": safe_float(row.volatility_score),
        "quality": _quality_for_peer(row),
    }

    total = 0.0
    weights = 0.0

    for name, value in raw.items():
        pct = _percentile(
            value,
            distributions.get(name, []),
        )

        if pct is None:
            continue

        weight = FORM_WEIGHTS[name]
        total += pct * weight
        weights += weight

    if weights <= 0:
        return None

    return round(
        clamp(total / weights),
        2,
    )


def classify_form_status(
    form_score,
    absolute_score,
    data_quality,
):
    if (
        form_score is None
        or data_quality is None
        or data_quality < 40
    ):
        return "UNRATED"

    if (
        form_score >= FORM_THRESHOLDS["IN_FORM"]
        and data_quality >= 65
        and (
            absolute_score is None
            or absolute_score >= 55
        )
    ):
        return "IN_FORM"

    if form_score >= FORM_THRESHOLDS["ON_TRACK"]:
        return "ON_TRACK"

    if form_score >= FORM_THRESHOLDS["OFF_TRACK"]:
        return "OFF_TRACK"

    return "NOT_IN_FORM"


def _peer_summary(
    status,
    absolute_score,
    form_score,
    peer_group,
):
    if status == "UNRATED":
        return (
            "Insufficient reliable data is available to assign "
            "a category-relative Fund Form rating."
        )

    parts = []

    if absolute_score is not None:
        parts.append(
            "TopOne Fund Health Score: "
            f"{round(absolute_score, 1)}/100."
        )

    if form_score is not None:
        parts.append(
            "Category-relative Form Score: "
            f"{round(form_score, 1)}/100 within {peer_group}."
        )

    messages = {
        "IN_FORM":
            "The fund currently ranks among the stronger members "
            "of its peer category across the available performance, "
            "consistency and risk signals.",

        "ON_TRACK":
            "The fund is currently performing within a healthy "
            "range compared with similar funds.",

        "OFF_TRACK":
            "The fund is currently trailing stronger members of "
            "its peer category and should be monitored.",

        "NOT_IN_FORM":
            "The fund currently ranks among the weaker members of "
            "its peer category on the available signals.",
    }

    parts.append(messages[status])

    return " ".join(parts)



def normalize_scheme_identity(product):
    """
    Build an underlying-scheme identity used only for peer ranking.

    Goal:
        Direct Growth / Direct IDCW / Regular Growth / Regular IDCW
        variants of the same underlying scheme should not each count as
        separate peer observations.

    This is a heuristic until the fund-master pipeline stores a dedicated
    canonical scheme-family identifier.
    """

    name = (
        str(getattr(product, "name", "") or "")
        .lower()
    )

    # Common plan / option fragments that should not define a distinct
    # underlying scheme for peer-ranking purposes.
    patterns = [
        r"\bdirect plan\b",
        r"\bregular plan\b",
        r"\binstitutional plan\b",
        r"\bwealth plan\b",
        r"\bdirect\b",
        r"\bregular\b",
        r"\binstitutional\b",
        r"\bgrowth option\b",
        r"\bgrowth plan\b",
        r"\bgrowth\b",
        r"\bidcw option\b",
        r"\bidcw\b",
        r"\bdividend option\b",
        r"\bdividend\b",
        r"\bpayout of income distribution cum capital withdrawal option\b",
        r"\breinvestment of income distribution cum capital withdrawal option\b",
        r"\bincome distribution cum capital withdrawal\b",
        r"\bbonus option\b",
        r"\bbonus\b",
        r"\bplan\b",
        r"\boption\b",
    ]

    for pattern in patterns:
        name = re.sub(
            pattern,
            " ",
            name,
            flags=re.IGNORECASE,
        )

    # Remove punctuation noise and duplicate spaces.
    name = re.sub(
        r"[^a-z0-9]+",
        " ",
        name,
    )

    name = re.sub(
        r"\s+",
        " ",
        name,
    ).strip()

    # Provider is included to reduce accidental collisions between
    # similarly named schemes from different AMCs.
    provider = (
        str(
            getattr(
                product,
                "provider",
                "",
            )
            or ""
        )
        .lower()
        .strip()
    )

    return (
        provider,
        name,
        get_peer_group(product),
    )


def choose_scheme_representative(rows):
    """
    Pick one representative row for an underlying scheme.

    Preference order:
        1. Direct + Growth
        2. Direct
        3. Growth
        4. Better data quality
        5. Lower id for deterministic tie-breaking
    """

    def score(row):
        text = (
            str(
                getattr(
                    row,
                    "name",
                    "",
                )
                or ""
            )
            .lower()
        )

        direct = (
            "direct" in text
        )

        growth = (
            "growth" in text
        )

        data_quality = (
            safe_float(
                getattr(
                    row,
                    "data_quality_score",
                    None,
                )
            )
            or 0.0
        )

        return (
            1 if (
                direct
                and growth
            ) else 0,
            1 if direct else 0,
            1 if growth else 0,
            data_quality,
            -int(
                getattr(
                    row,
                    "id",
                    0,
                )
            ),
        )

    return max(
        rows,
        key=score,
    )


def collapse_to_underlying_schemes(rows):
    """
    Collapse plan/option variants into one representative row.

    Returns:
        representatives
        representative_by_product_id
    """

    grouped = defaultdict(list)

    for row in rows:
        grouped[
            normalize_scheme_identity(
                row
            )
        ].append(row)

    representatives = []
    representative_by_product_id = {}

    for group_rows in grouped.values():
        representative = (
            choose_scheme_representative(
                group_rows
            )
        )

        representatives.append(
            representative
        )

        for row in group_rows:
            representative_by_product_id[
                row.id
            ] = representative

    return (
        representatives,
        representative_by_product_id,
    )


def final_percentile_from_composite(
    value,
    sorted_values,
):
    """
    Rank the weighted composite one final time inside the peer group.

    This removes the upward compression created when individually
    percentiled components are averaged together.

    Result:
        0-100 final Form percentile
    """

    return _percentile(
        value,
        sorted_values,
    )


def apply_peer_form_rankings(
    db: Session,
    batch_size: int = 250,
):
    """
    Final category-relative Fund Form engine.

    Improvements over the previous pass:

    1. UNRATED funds are excluded from ranking.
    2. Plan/option duplicates are collapsed to one underlying scheme
       representative for percentile calculations.
    3. Each representative gets a weighted composite of component
       percentiles.
    4. That composite is ranked one more time inside the peer group.
       The resulting final percentile is the stored peer_percentile.
    5. The representative's final status is copied to all of that
       scheme's plan/option variants.

    Final thresholds:
        IN_FORM      >= 80
        ON_TRACK     >= 50
        OFF_TRACK    >= 20
        NOT_IN_FORM  < 20

    IN_FORM guardrails:
        fund_health_score >= 55
        data_quality_score >= 65
    """

    rows = (
        db.query(
            InvestmentProduct.id,
            InvestmentProduct.name,
            InvestmentProduct.provider,
            InvestmentProduct.category,
            InvestmentProduct.sub_category,
            InvestmentProduct.asset_class,
            InvestmentProduct.fund_health_score,
            InvestmentProduct.data_quality_score,
            InvestmentProduct.long_term_score,
            InvestmentProduct.consistency_score,
            InvestmentProduct.risk_adjusted_score,
            InvestmentProduct.downside_score,
            InvestmentProduct.volatility_score,
            InvestmentProduct.momentum_score,
            InvestmentProduct.expense_ratio,
            InvestmentProduct.aum,
        )
        .filter(
            InvestmentProduct.is_active
            == True
        )
        .all()
    )

    # --------------------------------------------------------
    # ELIGIBILITY
    # --------------------------------------------------------

    eligible_rows = []
    unrated_ids = set()

    for row in rows:
        health = safe_float(
            row.fund_health_score
        )
        quality = safe_float(
            row.data_quality_score
        )

        if (
            health is None
            or quality is None
            or quality < 40
        ):
            unrated_ids.add(
                row.id
            )
            continue

        eligible_rows.append(
            row
        )

    # --------------------------------------------------------
    # COLLAPSE PLAN / OPTION VARIANTS
    # --------------------------------------------------------

    (
        representatives,
        representative_by_product_id,
    ) = collapse_to_underlying_schemes(
        eligible_rows
    )

    # --------------------------------------------------------
    # BUILD REPRESENTATIVE PEER GROUPS
    # --------------------------------------------------------

    specific_groups = defaultdict(list)
    family_groups = defaultdict(list)

    for row in representatives:
        specific_groups[
            get_peer_group(row)
        ].append(row)

        family_groups[
            get_peer_family(row)
        ].append(row)

    effective_group = {}

    for row in representatives:
        specific = (
            get_peer_group(row)
        )
        family = (
            get_peer_family(row)
        )

        specific_rows = (
            specific_groups[
                specific
            ]
        )

        family_rows = (
            family_groups[
                family
            ]
        )

        if (
            len(specific_rows)
            >= MIN_PEER_GROUP_SIZE
        ):
            effective_group[
                row.id
            ] = (
                specific,
                specific_rows,
            )

        elif (
            len(family_rows)
            >= MIN_PEER_GROUP_SIZE
        ):
            effective_group[
                row.id
            ] = (
                f"{family}:FAMILY_FALLBACK",
                family_rows,
            )

        else:
            unrated_ids.add(
                row.id
            )

    representatives = [
        row
        for row in representatives
        if row.id not in unrated_ids
    ]

    # --------------------------------------------------------
    # COMPONENT DISTRIBUTIONS PER EFFECTIVE GROUP
    # --------------------------------------------------------

    distributions = {}

    for row in representatives:
        group_name, group_rows = (
            effective_group[
                row.id
            ]
        )

        if (
            group_name
            in distributions
        ):
            continue

        distributions[
            group_name
        ] = {
            "long_term":
                _sorted_values(
                    item.long_term_score
                    for item in group_rows
                    if item.id not in unrated_ids
                ),

            "consistency":
                _sorted_values(
                    item.consistency_score
                    for item in group_rows
                    if item.id not in unrated_ids
                ),

            "risk_adjusted":
                _sorted_values(
                    item.risk_adjusted_score
                    for item in group_rows
                    if item.id not in unrated_ids
                ),

            "momentum":
                _sorted_values(
                    item.momentum_score
                    for item in group_rows
                    if item.id not in unrated_ids
                ),

            "downside":
                _sorted_values(
                    item.downside_score
                    for item in group_rows
                    if item.id not in unrated_ids
                ),

            "volatility":
                _sorted_values(
                    item.volatility_score
                    for item in group_rows
                    if item.id not in unrated_ids
                ),

            "quality":
                _sorted_values(
                    _quality_for_peer(
                        item
                    )
                    for item in group_rows
                    if item.id not in unrated_ids
                ),
        }

    # --------------------------------------------------------
    # FIRST PASS: WEIGHTED COMPOSITE
    # --------------------------------------------------------

    composite_by_rep_id = {}

    for row in representatives:
        group_name, _ = (
            effective_group[
                row.id
            ]
        )

        composite = (
            calculate_peer_form_score(
                row,
                distributions[
                    group_name
                ],
            )
        )

        if composite is None:
            unrated_ids.add(
                row.id
            )
            continue

        composite_by_rep_id[
            row.id
        ] = composite

    representatives = [
        row
        for row in representatives
        if row.id in composite_by_rep_id
    ]

    # --------------------------------------------------------
    # SECOND PASS: FINAL COMPOSITE PERCENTILE
    # --------------------------------------------------------

    composite_distributions = (
        defaultdict(list)
    )

    for row in representatives:
        group_name, _ = (
            effective_group[
                row.id
            ]
        )

        composite_distributions[
            group_name
        ].append(
            composite_by_rep_id[
                row.id
            ]
        )

    for group_name in list(
        composite_distributions.keys()
    ):
        composite_distributions[
            group_name
        ] = sorted(
            composite_distributions[
                group_name
            ]
        )

    representative_result = {}

    for row in representatives:
        group_name, _ = (
            effective_group[
                row.id
            ]
        )

        composite = (
            composite_by_rep_id[
                row.id
            ]
        )

        final_form_percentile = (
            final_percentile_from_composite(
                composite,
                composite_distributions[
                    group_name
                ],
            )
        )

        status = (
            classify_form_status(
                form_score=(
                    final_form_percentile
                ),
                absolute_score=safe_float(
                    row.fund_health_score
                ),
                data_quality=safe_float(
                    row.data_quality_score
                ),
            )
        )

        representative_result[
            row.id
        ] = {
            "group":
                group_name,

            "composite":
                composite,

            "form_score":
                round(
                    final_form_percentile,
                    2,
                )
                if final_form_percentile
                is not None
                else None,

            "status":
                status,
        }

    # --------------------------------------------------------
    # MAP REPRESENTATIVE RESULT TO EVERY PLAN/OPTION VARIANT
    # --------------------------------------------------------

    ranking = {}

    for row in eligible_rows:
        representative = (
            representative_by_product_id[
                row.id
            ]
        )

        if (
            representative.id
            in unrated_ids
            or representative.id
            not in representative_result
        ):
            unrated_ids.add(
                row.id
            )
            continue

        ranking[
            row.id
        ] = representative_result[
            representative.id
        ]

    # --------------------------------------------------------
    # UPDATE DATABASE
    # --------------------------------------------------------

    all_ids = sorted(
        row.id
        for row in rows
    )

    updated = 0
    status_counts = (
        defaultdict(int)
    )

    for start in range(
        0,
        len(all_ids),
        batch_size,
    ):
        batch_ids = (
            all_ids[
                start:
                start + batch_size
            ]
        )

        products = (
            db.query(
                InvestmentProduct
            )
            .filter(
                InvestmentProduct.id.in_(
                    batch_ids
                )
            )
            .all()
        )

        for product in products:

            if (
                product.id
                in unrated_ids
                or product.id
                not in ranking
            ):
                product.peer_percentile = (
                    None
                )

                product.fund_status = (
                    "UNRATED"
                )

                product.fund_health_summary = (
                    "Insufficient reliable data is "
                    "available to assign a "
                    "category-relative Fund Form rating."
                )

                product.health_calculated_at = (
                    datetime.utcnow()
                )

                status_counts[
                    "UNRATED"
                ] += 1

                updated += 1

                components = {
                    "long_term":
                        product.long_term_score,

                    "consistency":
                        product.consistency_score,

                    "risk_adjusted":
                        product.risk_adjusted_score,

                    "downside":
                        product.downside_score,

                    "volatility":
                        product.volatility_score,

                    "momentum":
                        product.momentum_score,

                    "peer":
                        None,

                    "quality":
                        calculate_quality_score(
                            safe_float(
                                product.expense_ratio
                            ),
                            safe_float(
                                product.aum
                            ),
                        ),

                    "fundamental":
                        None,

                    "news":
                        calculate_news_score(
                            product=product
                        ),
                }

                save_fund_health_snapshot(
                    db=db,
                    product=product,
                    score=(
                        product.fund_health_score
                    ),
                    status="UNRATED",
                    history_days=0,
                    data_quality=(
                        product.data_quality_score
                        or 0.0
                    ),
                    components=components,
                )

                continue

            result = ranking[
                product.id
            ]

            product.peer_percentile = (
                result[
                    "form_score"
                ]
            )

            product.fund_status = (
                result[
                    "status"
                ]
            )

            product.fund_health_summary = (
                _peer_summary(
                    status=(
                        result["status"]
                    ),
                    absolute_score=safe_float(
                        product.fund_health_score
                    ),
                    form_score=(
                        result[
                            "form_score"
                        ]
                    ),
                    peer_group=(
                        result["group"]
                    ),
                )
            )

            product.health_calculated_at = (
                datetime.utcnow()
            )

            components = {
                "long_term":
                    product.long_term_score,

                "consistency":
                    product.consistency_score,

                "risk_adjusted":
                    product.risk_adjusted_score,

                "downside":
                    product.downside_score,

                "volatility":
                    product.volatility_score,

                "momentum":
                    product.momentum_score,

                "peer":
                    product.peer_percentile,

                "quality":
                    calculate_quality_score(
                        safe_float(
                            product.expense_ratio
                        ),
                        safe_float(
                            product.aum
                        ),
                    ),

                "fundamental":
                    None,

                "news":
                    calculate_news_score(
                        product=product
                    ),
            }

            save_fund_health_snapshot(
                db=db,
                product=product,
                score=(
                    product.fund_health_score
                ),
                status=(
                    product.fund_status
                ),
                history_days=(
                    MIN_HISTORY_DAYS
                ),
                data_quality=(
                    product.data_quality_score
                    or 0.0
                ),
                components=components,
            )

            status_counts[
                product.fund_status
            ] += 1

            updated += 1

        db.commit()
        db.expunge_all()

        print(
            "Peer Form progress: "
            f"{updated}/"
            f"{len(all_ids)}"
        )

    return {
        "total_products":
            len(rows),

        "eligible_products":
            len(rows)
            - len(
                unrated_ids
            ),

        "underlying_schemes":
            len(
                representatives
            ),

        "unrated_products":
            len(
                unrated_ids
            ),

        "updated":
            updated,

        "peer_groups":
            len(
                distributions
            ),

        "status_counts":
            dict(
                status_counts
            ),
    }


# ============================================================
# FUND HEALTH SNAPSHOT HISTORY
# ============================================================

def save_fund_health_snapshot(
    db: Session,
    product: InvestmentProduct,
    *,
    score,
    status,
    history_days,
    data_quality,
    components,
):
    """
    Store one Fund Health snapshot per fund per UTC day.

    If Fund Health is recalculated multiple times on the same day,
    the same daily snapshot is updated rather than duplicated.

    This history powers the Fund Radar status timeline and can later
    become a clean feature source for ML transition/deterioration models.
    """

    snapshot_date = datetime.utcnow().date()

    snapshot = (
        db.query(FundHealthHistory)
        .filter(
            FundHealthHistory.product_id == product.id,
            FundHealthHistory.snapshot_date == snapshot_date,
        )
        .first()
    )

    if snapshot is None:
        snapshot = FundHealthHistory(
            product_id=product.id,
            snapshot_date=snapshot_date,
        )
        db.add(snapshot)

    components = components or {}

    snapshot.fund_health_score = score
    snapshot.fund_status = status
    snapshot.history_days = history_days
    snapshot.data_quality_score = data_quality

    snapshot.long_term_score = components.get("long_term")
    snapshot.consistency_score = components.get("consistency")
    snapshot.risk_adjusted_score = components.get("risk_adjusted")
    snapshot.downside_score = components.get("downside")
    snapshot.volatility_score = components.get("volatility")
    snapshot.momentum_score = components.get("momentum")
    snapshot.peer_percentile = components.get("peer")
    snapshot.quality_score = components.get("quality")
    snapshot.fundamental_score = components.get("fundamental")
    snapshot.news_score = components.get("news")

    snapshot.fund_health_summary = product.fund_health_summary
    snapshot.calculated_at = product.health_calculated_at or datetime.utcnow()

    return snapshot


# ============================================================
# CALCULATE ONE FUND
# ============================================================

def calculate_product_health(
    db: Session,
    product: InvestmentProduct,
):
    """
    Calculate complete Fund Health for one fund.

    Pipeline:

        NAV History
             ↓
        Returns
             ↓
        Risk Metrics
             ↓
        Momentum
             ↓
        Long-Term Performance
             ↓
        Quality
             ↓
        Fundamental Data
             ↓
        Peer Score
             ↓
        News Intelligence
             ↓
        Weighted Fund Health Score
             ↓
        Fund Status
    """

    # ========================================================
    # FETCH HISTORY
    # ========================================================

    rows = get_nav_history(
        db=db,
        product_id=product.id,
    )

    history_days = len(
        rows
    )

    data_quality = (
        calculate_data_quality(
            rows
        )
    )

    # ========================================================
    # INSUFFICIENT DATA
    # ========================================================

    if (
        history_days
        < MIN_HISTORY_DAYS
    ):

        product.fund_health_score = None

        product.fund_status = (
            "UNRATED"
        )

        product.consistency_score = None
        product.rolling_return_score = None
        product.risk_adjusted_score = None
        product.downside_score = None
        product.volatility_score = None
        product.momentum_score = None
        product.long_term_score = None
        product.data_quality_score = (
            data_quality
        )

        product.peer_percentile = None

        product.fund_health_summary = (
            "Insufficient historical data is "
            "available to reliably assess this fund."
        )

        product.health_calculated_at = (
            datetime.utcnow()
        )

        save_fund_health_snapshot(
            db=db,
            product=product,
            score=None,
            status="UNRATED",
            history_days=history_days,
            data_quality=data_quality,
            components={},
        )

        return {
            "product_id": product.id,
            "score": None,
            "status": "UNRATED",
            "history_days": history_days,
            "data_quality": data_quality,
            "components": {},
        }

    # ========================================================
    # DAILY RETURNS
    # ========================================================

    daily_returns = (
        calculate_daily_returns(
            rows
        )
    )

    # ========================================================
    # RISK METRICS
    # ========================================================

    calculated_volatility = (
        calculate_volatility(
            daily_returns
        )
    )

    calculated_sharpe = (
        calculate_sharpe(
            daily_returns
        )
    )

    max_drawdown = (
        calculate_max_drawdown(
            rows
        )
    )

    # ========================================================
    # RETURNS
    # ========================================================

    return_1y = (
        safe_float(
            product.return_1y
        )
    )

    return_3y = (
        safe_float(
            product.return_3y
        )
    )

    return_5y = (
        safe_float(
            product.return_5y
        )
    )

    # ========================================================
    # FALLBACK: CALCULATE FROM NAV HISTORY
    # ========================================================

    if return_1y is None:

        return_1y = (
            calculate_annualized_return(
                rows,
                365,
            )
        )

    if return_3y is None:

        return_3y = (
            calculate_annualized_return(
                rows,
                1095,
            )
        )

    if return_5y is None:

        return_5y = (
            calculate_annualized_return(
                rows,
                1825,
            )
        )

    # ========================================================
    # COMPONENT SCORES
    # ========================================================

    consistency = (
        calculate_consistency(
            daily_returns
        )
    )

    rolling_return_score = (
        calculate_long_term_score(
            return_1y,
            return_3y,
            return_5y,
        )
    )

    risk_adjusted = (
        calculate_risk_adjusted_score(
            calculated_sharpe
            if calculated_sharpe is not None
            else safe_float(
                product.sharpe_ratio
            ),
            safe_float(
                product.alpha
            ),
        )
    )

    downside = (
        calculate_downside_score(
            max_drawdown
        )
    )

    volatility_score = (
        calculate_volatility_score(
            calculated_volatility
            if calculated_volatility is not None
            else safe_float(
                product.volatility
            ),
        )
    )

    momentum = (
        calculate_momentum(
            rows
        )
    )

    long_term = (
        calculate_long_term_score(
            return_1y,
            return_3y,
            return_5y,
        )
    )

    quality = (
        calculate_quality_score(
            safe_float(
                product.expense_ratio
            ),
            safe_float(
                product.aum
            ),
        )
    )

    fundamental = (
        calculate_fundamental_score(
            safe_float(
                product.equity_percentage
            ),
            safe_float(
                product.debt_percentage
            ),
            safe_float(
                product.cash_percentage
            ),
            safe_float(
                product.large_cap_percentage
            ),
            safe_float(
                product.mid_cap_percentage
            ),
            safe_float(
                product.small_cap_percentage
            ),
        )
    )

    # ========================================================
    # NEWS INTELLIGENCE
    # ========================================================

    news = calculate_news_score(
        product=product
    )

    # ========================================================
    # STORE COMPONENT SCORES
    # ========================================================

    product.consistency_score = (
        consistency
    )

    product.rolling_return_score = (
        rolling_return_score
    )

    product.risk_adjusted_score = (
        risk_adjusted
    )

    product.downside_score = (
        downside
    )

    product.volatility_score = (
        volatility_score
    )

    product.momentum_score = (
        momentum
    )

    product.long_term_score = (
        long_term
    )

    product.data_quality_score = (
        data_quality
    )

    # ========================================================
    # PEER SCORE
    # ========================================================
    #
    # IMPORTANT:
    #
    # The global peer engine will later calculate
    # true category-relative percentile scores.
    #
    # For now we use a neutral value.
    #
    # This means peer comparison does NOT artificially
    # distort the current score.
    #
    # ========================================================

    peer_score = 50.0

    product.peer_percentile = (
        peer_score
    )

    # ========================================================
    # ALL COMPONENTS
    # ========================================================

    components = {
        "long_term": long_term,
        "consistency": consistency,
        "risk_adjusted": risk_adjusted,
        "downside": downside,
        "volatility": volatility_score,
        "momentum": momentum,
        "peer": peer_score,
        "quality": quality,
        "fundamental": fundamental,
        "news": news,
    }

    # ========================================================
    # WEIGHTED SCORE
    # ========================================================

    weighted_sum = 0.0
    weight_sum = 0.0

    for name, value in components.items():

        if value is None:
            continue

        weight = WEIGHTS[
            name
        ]

        weighted_sum += (
            value
            * weight
        )

        weight_sum += (
            weight
        )

    if weight_sum <= 0:

        score = None

    else:

        score = (
            weighted_sum
            / weight_sum
        )

    if score is not None:

        score = round(
            clamp(score),
            2,
        )

    # ========================================================
    # STATUS
    # ========================================================

    status = classify_status(
        score=score,
        data_quality=data_quality,
        history_days=history_days,
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = (
        generate_health_summary(
            status=status,
            score=score,
            momentum=momentum,
            volatility=(
                calculated_volatility
                if calculated_volatility
                is not None
                else safe_float(
                    product.volatility
                )
            ),
            max_drawdown=max_drawdown,
        )
    )

    # ========================================================
    # SAVE FINAL RESULTS
    # ========================================================

    product.fund_health_score = (
        score
    )

    product.fund_status = (
        status
    )

    product.fund_health_summary = (
        summary
    )

    product.health_calculated_at = (
        datetime.utcnow()
    )

    save_fund_health_snapshot(
        db=db,
        product=product,
        score=score,
        status=status,
        history_days=history_days,
        data_quality=data_quality,
        components=components,
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "product_id": product.id,
        "score": score,
        "status": status,
        "history_days": history_days,
        "data_quality": data_quality,
        "components": components,
    }


# ============================================================
# CALCULATE SELECTED FUNDS
# ============================================================

def calculate_fund_health_for_products(
    db: Session,
    product_ids,
    batch_size: int = 100,
):
    """
    Recalculate base Fund Health only for selected active products.

    This updates:
    - fund_health_score
    - component scores
    - provisional fund_status
    - fund_health_summary
    - health_calculated_at
    - FundHealthHistory snapshot

    Final category-relative peer ranking should be applied separately.
    """

    if not product_ids:
        return {
            "requested_products": 0,
            "eligible_products": 0,
            "processed": 0,
            "unrated": 0,
            "errors": 0,
            "peer_form": {
                "skipped": True,
                "reason": "No changed products.",
            },
        }

    clean_ids = sorted(
        {
            int(product_id)
            for product_id in product_ids
            if product_id is not None
        }
    )

    requested = len(clean_ids)

    eligible = (
        db.query(
            InvestmentProduct.id
        )
        .filter(
            InvestmentProduct.id.in_(
                clean_ids
            ),
            InvestmentProduct.is_active
            == True,
        )
        .count()
    )

    processed = 0
    unrated = 0
    errors = 0

    for offset in range(
        0,
        len(clean_ids),
        batch_size,
    ):
        batch_ids = clean_ids[
            offset:
            offset + batch_size
        ]

        products = (
            db.query(
                InvestmentProduct
            )
            .filter(
                InvestmentProduct.id.in_(
                    batch_ids
                ),
                InvestmentProduct.is_active
                == True,
            )
            .order_by(
                InvestmentProduct.id.asc()
            )
            .all()
        )

        for product in products:
            product_id = product.id

            try:
                result = (
                    calculate_product_health(
                        db=db,
                        product=product,
                    )
                )

                if (
                    result.get("status")
                    == "UNRATED"
                ):
                    unrated += 1

                processed += 1

            except Exception as exc:
                errors += 1

                print(
                    "Incremental Fund Health "
                    f"calculation failed for "
                    f"product {product_id}: "
                    f"{exc}"
                )

                db.rollback()

        db.commit()
        db.expunge_all()

    # ========================================================
    # CATEGORY-RELATIVE PEER SAFETY PASS
    # ========================================================
    #
    # Fund Health status is relative to the peer distribution.
    # Recomputing only changed funds and leaving peer percentiles
    # untouched would make rankings stale.
    #
    # The expensive per-fund NAV/health calculations above remain
    # incremental. This peer pass works from already-computed score
    # columns and is therefore substantially cheaper than rebuilding
    # all historical health metrics.
    # ========================================================

    peer_result = (
        apply_peer_form_rankings(
            db=db,
            batch_size=max(
                batch_size,
                100,
            ),
        )
    )

    return {
        "requested_products":
            requested,

        "eligible_products":
            eligible,

        "processed":
            processed,

        "unrated":
            unrated,

        "errors":
            errors,

        "peer_form":
            peer_result,
    }


# ============================================================
# CALCULATE ALL FUNDS
# ============================================================

def calculate_all_fund_health(
    db: Session,
    batch_size: int = 100,
):
    """
    Calculate Fund Health for all active funds.

    IMPORTANT:

    This uses ID-based pagination instead of:

        .all()

    for all 14k+ funds.

    It also commits every batch and expunges
    processed ORM objects.

    This prevents the SQLAlchemy identity-map /
    memory problem encountered during the first run.
    """

    # ========================================================
    # TOTAL
    # ========================================================

    total = (
        db.query(
            InvestmentProduct
        )
        .filter(
            InvestmentProduct.is_active
            == True
        )
        .count()
    )

    processed = 0
    unrated = 0
    errors = 0

    last_id = 0

    # ========================================================
    # BATCH LOOP
    # ========================================================

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
                InvestmentProduct.id.asc()
            )
            .limit(
                batch_size
            )
            .all()
        )

        if not products:
            break

        # ====================================================
        # PROCESS BATCH
        # ====================================================

        for product in products:

            try:

                result = (
                    calculate_product_health(
                        db=db,
                        product=product,
                    )
                )

                if (
                    result["status"]
                    == "UNRATED"
                ):

                    unrated += 1

                processed += 1

                last_id = (
                    product.id
                )

            except Exception as exc:

                errors += 1

                print(
                    "Fund health error "
                    f"for product "
                    f"{product.id}: "
                    f"{exc}"
                )

                # Roll back only the failed
                # transaction state.
                db.rollback()

                last_id = (
                    product.id
                )

        # ====================================================
        # COMMIT BATCH
        # ====================================================

        db.commit()

        # ====================================================
        # CLEAR SQLALCHEMY SESSION
        # ====================================================

        db.expunge_all()

        # ====================================================
        # PROGRESS
        # ====================================================

        print(
            "Fund health progress: "
            f"{processed}/{total}"
        )

    # ========================================================
    # CATEGORY-RELATIVE FORM PASS
    # ========================================================

    peer_result = (
        apply_peer_form_rankings(
            db=db,
            batch_size=max(
                batch_size,
                100,
            ),
        )
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {
        "total_products": total,
        "processed": processed,
        "unrated": unrated,
        "errors": errors,
        "peer_form": peer_result,
    }
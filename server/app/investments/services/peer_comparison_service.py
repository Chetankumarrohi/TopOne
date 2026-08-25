from statistics import median

from sqlalchemy.orm import Session

from app.investments.models.investment_product import (
    InvestmentProduct,
)

from app.investments.services.fund_health_service import (
    collapse_to_underlying_schemes,
    get_peer_group,
)


PEER_GROUP_LABELS = {
    "EQUITY:LARGE": "Large Cap",
    "EQUITY:LARGE_MID": "Large & Mid Cap",
    "EQUITY:MID": "Mid Cap",
    "EQUITY:SMALL": "Small Cap",
    "EQUITY:FLEXI": "Flexi Cap",
    "EQUITY:MULTI": "Multi Cap",
    "EQUITY:ELSS": "ELSS",
    "EQUITY:FOCUSED": "Focused",
    "EQUITY:DIVIDEND_YIELD": "Dividend Yield",
    "EQUITY:VALUE": "Value",
    "EQUITY:SECTORAL_THEMATIC": "Sectoral / Thematic",
    "EQUITY:OTHER": "Other Equity",

    "DEBT:OVERNIGHT": "Overnight",
    "DEBT:LIQUID": "Liquid",
    "DEBT:ULTRA_SHORT": "Ultra Short Duration",
    "DEBT:LOW_DURATION": "Low Duration",
    "DEBT:MONEY_MARKET": "Money Market",
    "DEBT:SHORT": "Short Duration",
    "DEBT:MEDIUM": "Medium Duration",
    "DEBT:MEDIUM_LONG": "Medium to Long Duration",
    "DEBT:LONG": "Long Duration",
    "DEBT:DYNAMIC_BOND": "Dynamic Bond",
    "DEBT:CORPORATE_BOND": "Corporate Bond",
    "DEBT:CREDIT_RISK": "Credit Risk",
    "DEBT:BANKING_PSU": "Banking & PSU",
    "DEBT:FLOATER": "Floater",
    "DEBT:GILT": "Gilt",
    "DEBT:GILT_10Y": "Gilt 10Y Constant Duration",
    "DEBT:OTHER": "Other Debt",

    "HYBRID:AGGRESSIVE": "Aggressive Hybrid",
    "HYBRID:CONSERVATIVE": "Conservative Hybrid",
    "HYBRID:BALANCED_ADVANTAGE": "Balanced Advantage",
    "HYBRID:ARBITRAGE": "Arbitrage",
    "HYBRID:EQUITY_SAVINGS": "Equity Savings",
    "HYBRID:MULTI_ASSET": "Multi Asset",
    "HYBRID:OTHER": "Other Hybrid",

    "INDEX_ETF:GOLD": "Gold",
    "INDEX_ETF:ETF": "ETF",
    "INDEX_ETF:INDEX": "Index Fund",
    "INDEX_ETF:OTHER": "Other Index & ETF",

    "FOF:DOMESTIC": "FoF Domestic",
    "FOF:OVERSEAS": "FoF Overseas",
    "FOF:OTHER": "Other FoF",

    "OTHER:RETIREMENT": "Retirement",
    "OTHER:CHILDREN": "Children",
    "OTHER:CLOSE_ENDED": "Close Ended",
    "OTHER:INTERVAL": "Interval",
    "OTHER:GENERAL": "Other",
}


def _safe_float(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _median(values):
    clean = [
        float(value)
        for value in values
        if value is not None
    ]

    if not clean:
        return None

    return round(
        median(clean),
        4,
    )


def _difference(value, benchmark):
    if value is None or benchmark is None:
        return None

    return round(
        float(value) - float(benchmark),
        4,
    )


def _metric_payload(
    fund_value,
    peer_median,
    *,
    lower_is_better=False,
):
    difference = _difference(
        fund_value,
        peer_median,
    )

    if difference is None:
        comparison = "UNAVAILABLE"

    elif abs(difference) < 0.0001:
        comparison = "IN_LINE"

    elif lower_is_better:
        comparison = (
            "BETTER"
            if difference < 0
            else "WORSE"
        )

    else:
        comparison = (
            "BETTER"
            if difference > 0
            else "WORSE"
        )

    return {
        "fund": (
            round(float(fund_value), 4)
            if fund_value is not None
            else None
        ),
        "peer_median": peer_median,
        "difference": difference,
        "comparison": comparison,
    }


def calculate_peer_comparison(
    db: Session,
    product: InvestmentProduct,
):
    target_peer_group = get_peer_group(
        product
    )

    peer_rows = (
        db.query(InvestmentProduct)
        .filter(
            InvestmentProduct.is_active
            == True
        )
        .all()
    )

    same_group = [
        row
        for row in peer_rows
        if get_peer_group(row)
        == target_peer_group
    ]

    (
        representatives,
        representative_by_product_id,
    ) = collapse_to_underlying_schemes(
        same_group
    )

    target_representative = (
        representative_by_product_id.get(
            product.id
        )
    )

    rated_representatives = [
        row
        for row in representatives
        if (
            row.peer_percentile is not None
            and row.fund_status
            not in {
                None,
                "UNRATED",
            }
        )
    ]

    rated_representatives.sort(
        key=lambda row: (
            -float(row.peer_percentile),
            row.name.lower(),
        )
    )

    category_rank = None

    if (
        target_representative is not None
        and target_representative
        in rated_representatives
    ):
        category_rank = (
            rated_representatives.index(
                target_representative
            )
            + 1
        )

    category_size = len(
        rated_representatives
    )

    peer_return_1y = _median(
        row.return_1y
        for row in rated_representatives
    )

    peer_return_3y = _median(
        row.return_3y
        for row in rated_representatives
    )

    peer_return_5y = _median(
        row.return_5y
        for row in rated_representatives
    )

    peer_volatility = _median(
        row.volatility
        for row in rated_representatives
        if row.volatility is not None
    )

    peer_expense_ratio = _median(
        row.expense_ratio
        for row in rated_representatives
        if row.expense_ratio is not None
    )

    peer_sharpe_ratio = _median(
        row.sharpe_ratio
        for row in rated_representatives
        if row.sharpe_ratio is not None
    )

    return {
        "product_id": product.id,

        "peer_group":
            target_peer_group,

        "category_label":
            PEER_GROUP_LABELS.get(
                target_peer_group,
                target_peer_group,
            ),

        "category_rank":
            category_rank,

        "category_size":
            category_size,

        "fund_status":
            product.fund_status
            or "UNRATED",

        "metrics": {
            "return_1y":
                _metric_payload(
                    _safe_float(
                        product.return_1y
                    ),
                    peer_return_1y,
                ),

            "return_3y":
                _metric_payload(
                    _safe_float(
                        product.return_3y
                    ),
                    peer_return_3y,
                ),

            "return_5y":
                _metric_payload(
                    _safe_float(
                        product.return_5y
                    ),
                    peer_return_5y,
                ),

            "volatility":
                _metric_payload(
                    _safe_float(
                        product.volatility
                    ),
                    peer_volatility,
                    lower_is_better=True,
                ),

            "expense_ratio":
                _metric_payload(
                    _safe_float(
                        product.expense_ratio
                    ),
                    peer_expense_ratio,
                    lower_is_better=True,
                ),

            "sharpe_ratio":
                _metric_payload(
                    _safe_float(
                        product.sharpe_ratio
                    ),
                    peer_sharpe_ratio,
                ),
        },
    }

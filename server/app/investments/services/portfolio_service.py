from collections import defaultdict

from sqlalchemy.orm import Session

from app.investments.models.holding import (
    InvestmentHolding,
)


def round_money(value: float) -> float:
    return round(
        float(value or 0),
        2,
    )


def get_portfolio_summary(
    db: Session,
    user_id: int,
):
    holdings = (
        db.query(InvestmentHolding)
        .filter(
            InvestmentHolding.user_id == user_id,
            InvestmentHolding.sync_status == "ACTIVE",
        )
        .all()
    )

    # --------------------------------
    # Empty portfolio
    # --------------------------------

    if not holdings:
        return {
            "total_invested": 0,
            "current_value": 0,

            "total_gain": 0,
            "total_gain_percentage": 0,

            "number_of_holdings": 0,

            "mutual_fund_value": 0,
            "stock_value": 0,
            "etf_value": 0,
            "gold_value": 0,
            "debt_value": 0,
            "other_value": 0,

            "asset_allocation": [],
        }

    # --------------------------------
    # Portfolio totals
    # --------------------------------

    total_invested = sum(
        holding.invested_amount or 0
        for holding in holdings
    )

    current_value = sum(
        holding.current_value or 0
        for holding in holdings
    )

    total_gain = (
        current_value
        - total_invested
    )

    if total_invested > 0:
        total_gain_percentage = (
            total_gain
            / total_invested
        ) * 100
    else:
        total_gain_percentage = 0

    # --------------------------------
    # Asset values
    # --------------------------------

    values_by_type = defaultdict(float)

    for holding in holdings:
        asset_type = (
            holding.asset_type
            or "OTHER"
        ).upper()

        values_by_type[
            asset_type
        ] += (
            holding.current_value
            or 0
        )

    mutual_fund_value = (
        values_by_type["MUTUAL_FUND"]
    )

    stock_value = (
        values_by_type["STOCK"]
    )

    etf_value = (
        values_by_type["ETF"]
    )

    gold_value = (
        values_by_type["GOLD"]
    )

    debt_value = (
        values_by_type["BOND"]
        + values_by_type["PPF"]
        + values_by_type["EPF"]
        + values_by_type["NPS"]
    )

    known_value = (
        mutual_fund_value
        + stock_value
        + etf_value
        + gold_value
        + debt_value
    )

    other_value = max(
        current_value
        - known_value,
        0,
    )

    # --------------------------------
    # Allocation
    # --------------------------------

    asset_allocation = []

    for asset_type, value in sorted(
        values_by_type.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        if current_value > 0:
            percentage = (
                value
                / current_value
            ) * 100
        else:
            percentage = 0

        asset_allocation.append(
            {
                "asset_type":
                    asset_type,

                "value":
                    round_money(
                        value
                    ),

                "percentage":
                    round(
                        percentage,
                        2,
                    ),
            }
        )

    return {
        "total_invested":
            round_money(
                total_invested
            ),

        "current_value":
            round_money(
                current_value
            ),

        "total_gain":
            round_money(
                total_gain
            ),

        "total_gain_percentage":
            round(
                total_gain_percentage,
                2,
            ),

        "number_of_holdings":
            len(holdings),

        "mutual_fund_value":
            round_money(
                mutual_fund_value
            ),

        "stock_value":
            round_money(
                stock_value
            ),

        "etf_value":
            round_money(
                etf_value
            ),

        "gold_value":
            round_money(
                gold_value
            ),

        "debt_value":
            round_money(
                debt_value
            ),

        "other_value":
            round_money(
                other_value
            ),

        "asset_allocation":
            asset_allocation,
    }
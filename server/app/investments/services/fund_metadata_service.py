from datetime import datetime
from time import sleep

import requests

from sqlalchemy.orm import Session

from app.investments.models.investment_product import (
    InvestmentProduct,
)


MFDATA_BASE_URL = (
    "https://mfdata.in/api/v1"
)

REQUEST_TIMEOUT = 30


def _safe_float(value):
    if value is None:
        return None

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def fetch_scheme_metadata(
    scheme_code: str,
):
    """
    Fetch normalized metadata using AMFI scheme code.

    This is an enrichment source. NAV remains sourced
    from AMFI in the existing pipeline.
    """

    url = (
        f"{MFDATA_BASE_URL}"
        f"/schemes/{scheme_code}"
    )

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent":
                "TopOne/1.0",
        },
    )

    response.raise_for_status()

    payload = response.json()

    if (
        not isinstance(
            payload,
            dict,
        )
    ):
        return None

    data = payload.get(
        "data"
    )

    if not isinstance(
        data,
        dict,
    ):
        return None

    return data


def apply_scheme_metadata(
    product: InvestmentProduct,
    data: dict,
):
    """
    Map normalized metadata onto InvestmentProduct.

    Only overwrite fields when the source gives us
    a real value.
    """

    updated_fields = []

    # -----------------------------
    # AUM
    # -----------------------------

    aum = _safe_float(
        data.get("aum_cr")
        or data.get("aum")
    )

    if aum is not None:
        product.aum = aum

        updated_fields.append(
            "aum"
        )

    # -----------------------------
    # EXPENSE RATIO / TER
    # -----------------------------

    expense_ratio = (
        _safe_float(
            data.get(
                "expense_ratio"
            )
        )
    )

    if (
        expense_ratio
        is not None
    ):
        product.expense_ratio = (
            expense_ratio
        )

        updated_fields.append(
            "expense_ratio"
        )

    # -----------------------------
    # EXIT LOAD
    # -----------------------------

    exit_load = (
        data.get(
            "exit_load"
        )
    )

    if exit_load:
        product.exit_load = str(
            exit_load
        ).strip()

        updated_fields.append(
            "exit_load"
        )

    # -----------------------------
    # RISK / ANALYTICS
    # -----------------------------

    ratios = data.get(
        "ratios"
    )

    if isinstance(
        ratios,
        dict,
    ):

        sharpe = _safe_float(
            ratios.get(
                "sharpe"
            )
        )

        beta = _safe_float(
            ratios.get(
                "beta"
            )
        )

        alpha = _safe_float(
            ratios.get(
                "alpha"
            )
        )

        std_dev = _safe_float(
            ratios.get(
                "std_dev"
            )
            or ratios.get(
                "standard_deviation"
            )
        )

        if sharpe is not None:
            product.sharpe_ratio = (
                sharpe
            )

            updated_fields.append(
                "sharpe_ratio"
            )

        if beta is not None:
            product.beta = beta

            updated_fields.append(
                "beta"
            )

        if alpha is not None:
            product.alpha = alpha

            updated_fields.append(
                "alpha"
            )

        if std_dev is not None:
            product.standard_deviation = (
                std_dev
            )

            updated_fields.append(
                "standard_deviation"
            )

    # -----------------------------
    # CATEGORY
    # -----------------------------

    category = data.get(
        "category"
    )

    if (
        category
        and not product.sub_category
    ):
        product.sub_category = (
            str(category).strip()
        )

        updated_fields.append(
            "sub_category"
        )

    # -----------------------------
    # MIN INVESTMENT
    # -----------------------------

    minimum = _safe_float(
        data.get(
            "min_investment"
        )
    )

    if (
        minimum is not None
        and minimum > 0
        and (
            product.minimum_lumpsum
            is None
            or product.minimum_lumpsum
            == 0
        )
    ):
        product.minimum_lumpsum = (
            minimum
        )

        updated_fields.append(
            "minimum_lumpsum"
        )

    product.data_updated_at = (
        datetime.utcnow()
    )

    return updated_fields


def enrich_product_metadata(
    db: Session,
    product: InvestmentProduct,
):
    if not product.scheme_code:
        return {
            "status":
                "SKIPPED",

            "reason":
                "NO_SCHEME_CODE",
        }

    data = fetch_scheme_metadata(
        str(
            product.scheme_code
        )
    )

    if not data:
        return {
            "status":
                "NO_DATA",
        }

    updated_fields = (
        apply_scheme_metadata(
            product=product,
            data=data,
        )
    )

    return {
        "status":
            "UPDATED",

        "product_id":
            product.id,

        "scheme_code":
            product.scheme_code,

        "updated_fields":
            updated_fields,
    }


def sync_fund_metadata(
    db: Session,
    limit: int | None = None,
    delay_seconds: float = 0.05,
):
    """
    Enrich active mutual funds that already have an
    AMFI scheme code.

    Start with a small `limit` while testing.
    """

    query = (
        db.query(
            InvestmentProduct
        )
        .filter(
            InvestmentProduct.is_active
            == True,

            InvestmentProduct.scheme_code
            != None,
        )
        .order_by(
            InvestmentProduct.id.asc()
        )
    )

    if limit:
        query = query.limit(
            limit
        )

    products = query.all()

    processed = 0
    updated = 0
    no_data = 0
    failed = 0

    field_counts = {}

    for product in products:
        processed += 1

        try:
            result = (
                enrich_product_metadata(
                    db=db,
                    product=product,
                )
            )

            if (
                result.get(
                    "status"
                )
                == "UPDATED"
            ):
                updated += 1

                for field in (
                    result.get(
                        "updated_fields",
                        [],
                    )
                ):
                    field_counts[
                        field
                    ] = (
                        field_counts.get(
                            field,
                            0,
                        )
                        + 1
                    )

            elif (
                result.get(
                    "status"
                )
                == "NO_DATA"
            ):
                no_data += 1

        except (
            requests.RequestException,
            ValueError,
            TypeError,
        ):
            failed += 1

        if (
            processed % 50
            == 0
        ):
            db.commit()

            print(
                "Metadata progress: "
                f"{processed}/"
                f"{len(products)}"
            )

        if delay_seconds > 0:
            sleep(
                delay_seconds
            )

    db.commit()

    return {
        "processed":
            processed,

        "updated":
            updated,

        "no_data":
            no_data,

        "failed":
            failed,

        "fields_updated":
            field_counts,

        "synced_at":
            datetime.utcnow()
            .isoformat(),
    }

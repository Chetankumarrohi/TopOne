from datetime import datetime
from io import StringIO

from sqlalchemy.orm import Session

from app.investments.services.amfi_feed_service import (
    get_amfi_feed,
)

from app.investments.models.investment_product import (
    InvestmentProduct,
)

from app.investments.models.fund_nav_history import (
    FundNAVHistory,
)

def fetch_amfi_nav_file() -> str:
    

    return get_amfi_feed().content


def parse_nav_date(
    value: str,
):
    return datetime.strptime(
        value.strip(),
        "%d-%b-%Y",
    ).date()


def parse_amfi_records(
    content: str,
):
    records = []

    current_category = None
    current_amc = None

    for raw_line in StringIO(content):
        line = raw_line.strip()

        if not line:
            continue

        parts = line.split(";")

        # --------------------------------
        # Actual scheme row
        # --------------------------------

        if (
            len(parts) >= 6
            and parts[0].strip().isdigit()
        ):
            scheme_code = (
                parts[0].strip()
            )

            isin_growth_raw = (
                parts[1].strip()
            )

            isin_reinvestment_raw = (
                parts[2].strip()
            )

            isin_growth = (
                isin_growth_raw
                if isin_growth_raw
                not in {
                    "",
                    "-",
                }
                else None
            )

            isin_reinvestment = (
                isin_reinvestment_raw
                if isin_reinvestment_raw
                not in {
                    "",
                    "-",
                }
                else None
            )

            scheme_name = (
                parts[3].strip()
            )

            # Current AMFI NAVAll format:
            # 0 Scheme Code
            # 1 ISIN Div Payout / ISIN Growth
            # 2 ISIN Div Reinvestment
            # 3 Scheme Name
            # 4 Plan
            # 5 Option
            # 6 Net Asset Value
            # 7 Date
            if len(parts) >= 8:
                plan = (
                    parts[4].strip()
                    or None
                )

                option = (
                    parts[5].strip()
                    or None
                )

                nav_raw = (
                    parts[6].strip()
                )

                nav_date_raw = (
                    parts[7].strip()
                )

            else:
                # Backward compatibility with
                # older six-column AMFI rows.
                plan = None
                option = None

                nav_raw = (
                    parts[4].strip()
                )

                nav_date_raw = (
                    parts[5].strip()
                )

            try:
                nav = float(nav_raw)

                nav_date = parse_nav_date(
                    nav_date_raw
                )

            except (
                ValueError,
                TypeError,
            ):
                continue

            records.append(
                {
                    "scheme_code":
                        scheme_code,

                    "isin":
                        isin_growth,

                    "alternate_isin":
                        isin_reinvestment,

                    "scheme_name":
                        scheme_name,

                    "plan":
                        plan,

                    "option":
                        option,

                    "nav":
                        nav,

                    "nav_date":
                        nav_date,

                    "category":
                        current_category,

                    "amc":
                        current_amc,
                }
            )

            continue

        # --------------------------------
        # Headings
        # --------------------------------

        lower = line.lower()

        if (
            "open ended schemes"
            in lower
            or
            "close ended schemes"
            in lower
            or
            "interval fund"
            in lower
        ):
            current_category = line

        elif ";" not in line:
            current_amc = line

    return records


def infer_plan_type(
    scheme_name: str,
):
    name = scheme_name.lower()

    if "direct" in name:
        return "DIRECT"

    if "regular" in name:
        return "REGULAR"

    return None


def infer_option_type(
    scheme_name: str,
):
    name = scheme_name.lower()

    if "growth" in name:
        return "GROWTH"

    if "idcw" in name:
        return "IDCW"

    if "dividend" in name:
        return "IDCW"

    return None


def get_safe_isin(
    db: Session,
    isin: str | None,
    product_id: int | None = None,
):
    if (
        not isin
        or isin == "-"
    ):
        return None

    query = (
        db.query(InvestmentProduct)
        .filter(
            InvestmentProduct.isin
            == isin
        )
    )

    if product_id is not None:
        query = query.filter(
            InvestmentProduct.id
            != product_id
        )

    existing = query.first()

    if existing:
        return None

    return isin


def sync_amfi_fund_master(
    db: Session,
):
    try:
        snapshot = get_amfi_feed()
        content = snapshot.content

        records = parse_amfi_records(
            content
        )

        created = 0
        updated = 0
        nav_history_created = 0
        duplicate_isins_skipped = 0
        changed_product_ids = set()

        for record in records:
            product = (
                db.query(
                    InvestmentProduct
                )
                .filter(
                    InvestmentProduct.scheme_code
                    == record[
                        "scheme_code"
                    ]
                )
                .first()
            )

            # --------------------------------
            # Create new product
            # --------------------------------

            if not product:
                safe_isin = get_safe_isin(
                    db=db,
                    isin=record["isin"],
                )

                if (
                    record["isin"]
                    and safe_isin is None
                ):
                    duplicate_isins_skipped += 1

                product = InvestmentProduct(
                    name=record[
                        "scheme_name"
                    ],

                    product_type=
                        "MUTUAL_FUND",

                    scheme_code=record[
                        "scheme_code"
                    ],

                    isin=safe_isin,

                    provider=record[
                        "amc"
                    ],

                    category=record[
                        "category"
                    ],

                    plan_type=
                        infer_plan_type(
                            record[
                                "scheme_name"
                            ]
                        ),

                    option_type=
                        infer_option_type(
                            record[
                                "scheme_name"
                            ]
                        ),

                    nav=record[
                        "nav"
                    ],

                    nav_date=record[
                        "nav_date"
                    ],

                    previous_nav=None,

                    daily_change=None,

                    daily_change_percentage=None,

                    purchase_allowed=False,

                    sip_allowed=False,

                    source="AMFI",

                    data_updated_at=
                        datetime.utcnow(),
                )

                db.add(product)
                db.flush()

                created += 1
                changed_product_ids.add(product.id)

            # --------------------------------
            # Update existing product
            # --------------------------------

            else:
                previous_nav = (
                    product.nav
                    or 0
                )

                previous_nav_date = (
                    product.nav_date
                )

                new_nav = record[
                    "nav"
                ]

                new_nav_date = record[
                    "nav_date"
                ]

                # Calculate daily change only
                # when NAV date has actually changed.
                if (
                    new_nav > 0
                    and previous_nav > 0
                    and previous_nav_date
                    and new_nav_date
                    > previous_nav_date
                ):
                    daily_change = (
                        new_nav
                        - previous_nav
                    )

                    daily_change_percentage = (
                        daily_change
                        / previous_nav
                    ) * 100

                    product.previous_nav = (
                        previous_nav
                    )

                    product.daily_change = round(
                        daily_change,
                        4,
                    )

                    product.daily_change_percentage = round(
                        daily_change_percentage,
                        4,
                    )

                product.name = record[
                    "scheme_name"
                ]

                safe_isin = get_safe_isin(
                    db=db,
                    isin=record["isin"],
                    product_id=product.id,
                )

                if safe_isin:
                    product.isin = safe_isin

                elif record["isin"]:
                    duplicate_isins_skipped += 1

                product.provider = (
                    record[
                        "amc"
                    ]
                    or product.provider
                )

                product.category = (
                    record[
                        "category"
                    ]
                    or product.category
                )

                product.plan_type = (
                    infer_plan_type(
                        record[
                            "scheme_name"
                        ]
                    )
                )

                product.option_type = (
                    infer_option_type(
                        record[
                            "scheme_name"
                        ]
                    )
                )

                if (
                    new_nav > 0
                    and (
                        previous_nav_date is None
                        or new_nav_date
                        > previous_nav_date
                    )
                ):
                    product.nav = (
                        new_nav
                    )

                    product.nav_date = (
                        new_nav_date
                    )

                    product.data_updated_at = (
                        datetime.utcnow()
                    )

                    changed_product_ids.add(
                        product.id
                    )

                updated += 1

            # --------------------------------
            # NAV History
            # --------------------------------

            existing_history = (
                db.query(
                    FundNAVHistory
                )
                .filter(
                    FundNAVHistory.product_id
                    == product.id,

                    FundNAVHistory.nav_date
                    == record[
                        "nav_date"
                    ],
                )
                .first()
            )

            if (
                not existing_history
                and record["nav"] > 0
            ):
                history = FundNAVHistory(
                    product_id=
                        product.id,

                    nav_date=
                        record[
                            "nav_date"
                        ],

                    nav=
                        record[
                            "nav"
                        ],

                    daily_change=
                        product.daily_change,

                    daily_change_percentage=
                        product.daily_change_percentage,
                )

                db.add(history)

                nav_history_created += 1
                changed_product_ids.add(
                    product.id
                )

        db.commit()

        return {
            "records_received":
                len(records),

            "products_created":
                created,

            "products_updated":
                updated,

            "nav_history_created":
                nav_history_created,

            "duplicate_isins_skipped":
                duplicate_isins_skipped,

            "changed_product_ids":
                sorted(changed_product_ids),

            "changed_products":
                len(changed_product_ids),

            "synced_at":
                datetime.utcnow().isoformat(),
        }

    except Exception:
        db.rollback()
        raise
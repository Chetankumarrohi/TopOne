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



def parse_amfi_date(
    value: str,
):
    return datetime.strptime(
        value.strip(),
        "%d-%b-%Y",
    ).date()


def parse_amfi_nav_file(
    content: str,
):
    """
    Parse AMFI NAVAll.txt.

    Current AMFI format:

    0 Scheme Code
    1 ISIN Div Payout / ISIN Growth
    2 ISIN Div Reinvestment
    3 Scheme Name
    4 Plan
    5 Option
    6 Net Asset Value
    7 Date

    Older six-column AMFI rows are also
    supported for backward compatibility.
    """

    records = []

    for raw_line in StringIO(content):

        line = raw_line.strip()

        if not line:
            continue

        parts = line.split(";")

        if len(parts) < 6:
            continue

        scheme_code = (
            parts[0].strip()
        )

        # Skip headers, AMC names,
        # category headings, etc.
        if not scheme_code.isdigit():
            continue

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

        # -------------------------------------------------
        # CURRENT AMFI FORMAT
        # -------------------------------------------------

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

        # -------------------------------------------------
        # LEGACY AMFI FORMAT
        # -------------------------------------------------

        else:

            plan = None
            option = None

            nav_raw = (
                parts[4].strip()
            )

            nav_date_raw = (
                parts[5].strip()
            )

        try:
            nav = float(
                nav_raw
            )

            nav_date = (
                parse_amfi_date(
                    nav_date_raw
                )
            )

        except (
            ValueError,
            TypeError,
        ):
            continue

        # NAV cannot be negative.
        # Zero NAVs can exist in unusual/
        # segregated/defunct AMFI records,
        # so preserve them for classification.
        if nav < 0:
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
            }
        )

    return records


def update_product_nav(
    db: Session,
    product: InvestmentProduct,
    new_nav: float,
    nav_date,
):
    """
    Store NAV history and update the product's
    current NAV only when the incoming observation
    is newer than the currently stored NAV.

    Historical/older AMFI rows must never overwrite
    newer product-level NAV data.
    """

    # -----------------------------------------------------
    # SAFETY: NEVER MOVE CURRENT NAV BACKWARDS
    # -----------------------------------------------------

    if (
        product.nav_date is not None
        and nav_date < product.nav_date
    ):
        return False

    # -----------------------------------------------------
    # SAME DATE
    # -----------------------------------------------------

    existing_history = (
        db.query(
            FundNAVHistory
        )
        .filter(
            FundNAVHistory.product_id
            == product.id,

            FundNAVHistory.nav_date
            == nav_date,
        )
        .first()
    )

    if existing_history:

        # Same date already stored.
        #
        # Do not create duplicate history.
        # Also do not overwrite the current
        # product NAV unnecessarily.
        return False

    # -----------------------------------------------------
    # PREVIOUS NAV
    # -----------------------------------------------------

    previous_nav = (
        product.nav
        if product.nav is not None
        else 0.0
    )

    # -----------------------------------------------------
    # DAILY CHANGE
    # -----------------------------------------------------

    if (
        previous_nav > 0
        and new_nav > 0
    ):

        daily_change = (
            new_nav
            - previous_nav
        )

        daily_change_percentage = (
            daily_change
            / previous_nav
        ) * 100

    else:

        daily_change = 0.0
        daily_change_percentage = 0.0

    # -----------------------------------------------------
    # HISTORY
    # -----------------------------------------------------

    history = FundNAVHistory(
        product_id=product.id,

        nav_date=nav_date,

        nav=new_nav,

        daily_change=round(
            daily_change,
            4,
        ),

        daily_change_percentage=round(
            daily_change_percentage,
            4,
        ),
    )

    db.add(
        history
    )

    # -----------------------------------------------------
    # CURRENT PRODUCT NAV
    # -----------------------------------------------------

    product.previous_nav = (
        previous_nav
    )

    product.nav = (
        new_nav
    )

    product.nav_date = (
        nav_date
    )

    product.daily_change = round(
        daily_change,
        4,
    )

    product.daily_change_percentage = round(
        daily_change_percentage,
        4,
    )

    product.data_updated_at = (
        datetime.utcnow()
    )

    return True


def sync_amfi_navs(
    db: Session,
):
    """
    Fetch the current AMFI NAV feed and update
    InvestiGenie's active AMFI-mapped products.
    """

    content = (
        get_amfi_feed().content
    )

    records = (
        parse_amfi_nav_file(
            content
        )
    )

    records_received = len(
        records
    )

    updated = 0
    unmatched = 0
    stale_skipped = 0
    zero_nav_records = 0
    changed_product_ids = set()

    products = (
        db.query(
            InvestmentProduct
        )
        .filter(
            InvestmentProduct.is_active
            == True
        )
        .all()
    )

    # -----------------------------------------------------
    # LOOKUP MAPS
    # -----------------------------------------------------

    products_by_scheme_code = {
        str(product.scheme_code):
            product

        for product in products

        if product.scheme_code
    }

    products_by_isin = {
        product.isin:
            product

        for product in products

        if (
            product.isin
            and product.isin != "-"
        )
    }

    # -----------------------------------------------------
    # PROCESS AMFI RECORDS
    # -----------------------------------------------------

    for record in records:

        product = None

        scheme_code = (
            record[
                "scheme_code"
            ]
        )

        # Primary matching strategy:
        # AMFI scheme code.
        if (
            scheme_code
            in products_by_scheme_code
        ):
            product = (
                products_by_scheme_code[
                    scheme_code
                ]
            )

        # Secondary:
        # primary ISIN.
        elif (
            record["isin"]
            and record["isin"]
            in products_by_isin
        ):
            product = (
                products_by_isin[
                    record["isin"]
                ]
            )

        # Tertiary:
        # reinvestment ISIN.
        elif (
            record["alternate_isin"]
            and record["alternate_isin"]
            in products_by_isin
        ):
            product = (
                products_by_isin[
                    record[
                        "alternate_isin"
                    ]
                ]
            )

        if not product:
            unmatched += 1
            continue

        incoming_nav = (
            record["nav"]
        )

        incoming_date = (
            record["nav_date"]
        )

        # Zero NAV records are commonly associated with
        # segregated / legacy / defunct schemes.
        #
        # Keep count of them for lifecycle classification,
        # but never publish zero as a normal current NAV.
        if incoming_nav <= 0:
            zero_nav_records += 1
            continue

        # Explicitly track stale incoming rows.
        if (
            product.nav_date is not None
            and incoming_date
            < product.nav_date
        ):
            stale_skipped += 1
            continue

        changed = (
            update_product_nav(
                db=db,
                product=product,
                new_nav=incoming_nav,
                nav_date=incoming_date,
            )
        )

        if changed:
            updated += 1
            changed_product_ids.add(
                product.id
            )

    db.commit()

    return {
        "records_received":
            records_received,

        "products_updated":
            updated,

        "unmatched_records":
            unmatched,

        "stale_records_skipped":
            stale_skipped,

        "zero_nav_records":
            zero_nav_records,

        "changed_product_ids":
            sorted(changed_product_ids),

        "changed_products":
            len(changed_product_ids),

        "synced_at":
            datetime.utcnow().isoformat(),
    }
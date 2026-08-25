from datetime import date, datetime, timedelta
from io import StringIO
import time

import requests

from sqlalchemy import func
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

AMFI_HISTORY_URL = (
    "https://portal.amfiindia.com/"
    "DownloadNAVHistoryReport_Po.aspx"
)

AMFI_WINDOW_DAYS = 89

REQUEST_TIMEOUT = (
    15,   # connection timeout
    120,  # read timeout
)

MAX_REQUEST_RETRIES = 4

RETRY_SLEEP_SECONDS = 3


# ============================================================
# DATE HELPERS
# ============================================================

def subtract_years(
    value: date,
    years: int,
) -> date:
    """
    Subtract complete calendar years safely.

    Handles leap-day dates such as 29-Feb.
    """

    try:
        return value.replace(
            year=value.year - years
        )

    except ValueError:
        # 29-Feb -> 28-Feb
        return value.replace(
            month=2,
            day=28,
            year=value.year - years,
        )


# ============================================================
# FETCH HISTORICAL NAV
# ============================================================

def fetch_amfi_history(
    start_date: date,
    end_date: date,
) -> str:
    """
    Download one AMFI historical NAV window.

    Includes retry protection for temporary AMFI/network
    failures.
    """

    last_error = None

    for attempt in range(
        1,
        MAX_REQUEST_RETRIES + 1,
    ):

        try:

            response = requests.get(
                AMFI_HISTORY_URL,
                params={
                    "tp": "1",
                    "frmdt": (
                        start_date.strftime(
                            "%d-%b-%Y"
                        )
                    ),
                    "todt": (
                        end_date.strftime(
                            "%d-%b-%Y"
                        )
                    ),
                },
                timeout=REQUEST_TIMEOUT,
                headers={
                    "User-Agent":
                        "Mozilla/5.0 InvestiGenie/1.0",

                    "Accept":
                        "text/plain,text/html,*/*",
                },
            )

            response.raise_for_status()

            content = response.text

            if not content.strip():
                raise RuntimeError(
                    "AMFI returned an empty "
                    "historical NAV response."
                )

            return content

        except (
            requests.RequestException,
            RuntimeError,
        ) as exc:

            last_error = exc

            if attempt >= MAX_REQUEST_RETRIES:
                break

            wait_seconds = (
                RETRY_SLEEP_SECONDS * attempt
            )

            print(
                f"AMFI request failed for "
                f"{start_date} -> {end_date}. "
                f"Retry {attempt}/"
                f"{MAX_REQUEST_RETRIES} "
                f"in {wait_seconds}s..."
            )

            time.sleep(
                wait_seconds
            )

    raise RuntimeError(
        f"AMFI historical NAV request failed "
        f"for {start_date} -> {end_date}"
    ) from last_error


# ============================================================
# DATE PARSER
# ============================================================

def parse_history_date(
    value: str,
):
    value = value.strip()

    formats = [
        "%d-%b-%Y",
        "%d-%b-%Y %H:%M:%S",
    ]

    for date_format in formats:

        try:

            return datetime.strptime(
                value,
                date_format,
            ).date()

        except ValueError:
            continue

    raise ValueError(
        f"Invalid AMFI NAV date: {value}"
    )


# ============================================================
# PARSE AMFI RESPONSE
# ============================================================

def parse_historical_records(
    content: str,
):
    records = []

    for raw_line in StringIO(content):

        line = raw_line.strip()

        if not line:
            continue

        parts = [
            part.strip()
            for part in line.split(";")
        ]

        # AMFI historical format:
        #
        # 0 Scheme Code
        # 1 Scheme Name
        # 2 ISIN Payout/Growth
        # 3 ISIN Reinvestment
        # 4 NAV
        # 5 Repurchase Price
        # 6 Sale Price
        # 7 Date

        if len(parts) < 8:
            continue

        scheme_code = parts[0]

        if not scheme_code.isdigit():
            continue

        scheme_name = parts[1]

        nav_raw = parts[4]

        nav_date_raw = parts[7]

        if not nav_raw:
            continue

        try:

            nav = float(
                nav_raw
            )

            nav_date = (
                parse_history_date(
                    nav_date_raw
                )
            )

        except (
            ValueError,
            TypeError,
        ):
            continue

        if nav <= 0:
            continue

        records.append(
            {
                "scheme_code":
                    scheme_code,

                "scheme_name":
                    scheme_name,

                "nav":
                    nav,

                "nav_date":
                    nav_date,
            }
        )

    return records


# ============================================================
# PRODUCT MAP
# ============================================================

def build_product_map(
    db: Session,
):
    """
    Load AMFI scheme_code -> product_id once.

    This removes thousands/millions of repeated product
    queries during a historical backfill.
    """

    rows = (
        db.query(
            InvestmentProduct.id,
            InvestmentProduct.scheme_code,
        )
        .filter(
            InvestmentProduct.is_active
            == True,

            InvestmentProduct.scheme_code
            .isnot(None),
        )
        .all()
    )

    product_map = {}

    for (
        product_id,
        scheme_code,
    ) in rows:

        if not scheme_code:
            continue

        product_map[
            str(scheme_code).strip()
        ] = product_id

    return product_map


# ============================================================
# CONVERT AMFI RECORDS TO DB RECORDS
# ============================================================

def prepare_history_records(
    records: list[dict],
    product_map: dict,
):
    """
    Convert scheme-code records into DB-ready rows.

    Also removes duplicate product/date combinations from
    the incoming AMFI response.
    """

    prepared = {}

    missing_product = 0

    for record in records:

        scheme_code = str(
            record["scheme_code"]
        ).strip()

        product_id = (
            product_map.get(
                scheme_code
            )
        )

        if product_id is None:

            missing_product += 1

            continue

        key = (
            product_id,
            record["nav_date"],
        )

        prepared[key] = {
            "product_id":
                product_id,

            "nav_date":
                record["nav_date"],

            "nav":
                record["nav"],

            "daily_change":
                None,

            "daily_change_percentage":
                None,
        }

    return (
        list(prepared.values()),
        missing_product,
    )


# ============================================================
# BULK INSERT WITH DUPLICATE PROTECTION
# ============================================================

def bulk_insert_history_records(
    db: Session,
    rows: list[dict],
):
    """
    Insert historical NAV records in bulk.

    Uses the existing unique constraint:

        (product_id, nav_date)

    Duplicate records are ignored safely.
    """

    if not rows:

        return {
            "created": 0,
            "skipped_existing": 0,
        }

    bind = db.get_bind()

    dialect = (
        bind.dialect.name
    )

    # --------------------------------------------------------
    # SQLITE
    # --------------------------------------------------------

    if dialect == "sqlite":

        from sqlalchemy.dialects.sqlite import (
            insert as sqlite_insert,
        )

        statement = (
            sqlite_insert(
                FundNAVHistory.__table__
            )
            .on_conflict_do_nothing(
                index_elements=[
                    "product_id",
                    "nav_date",
                ]
            )
        )

    # --------------------------------------------------------
    # POSTGRESQL
    # --------------------------------------------------------

    elif dialect == "postgresql":

        from sqlalchemy.dialects.postgresql import (
            insert as postgres_insert,
        )

        statement = (
            postgres_insert(
                FundNAVHistory.__table__
            )
            .on_conflict_do_nothing(
                index_elements=[
                    "product_id",
                    "nav_date",
                ]
            )
        )

    else:

        raise RuntimeError(
            "Historical NAV bulk import currently "
            f"supports SQLite/PostgreSQL. "
            f"Current dialect: {dialect}"
        )

    # Count rows before this date range.
    min_date = min(
        row["nav_date"]
        for row in rows
    )

    max_date = max(
        row["nav_date"]
        for row in rows
    )

    before_count = (
        db.query(
            func.count(
                FundNAVHistory.id
            )
        )
        .filter(
            FundNAVHistory.nav_date
            >= min_date,

            FundNAVHistory.nav_date
            <= max_date,
        )
        .scalar()
        or 0
    )

    # SQLAlchemy executes this as efficient executemany.
    db.execute(
        statement,
        rows,
    )

    db.flush()

    after_count = (
        db.query(
            func.count(
                FundNAVHistory.id
            )
        )
        .filter(
            FundNAVHistory.nav_date
            >= min_date,

            FundNAVHistory.nav_date
            <= max_date,
        )
        .scalar()
        or 0
    )

    created = max(
        0,
        after_count - before_count,
    )

    skipped_existing = max(
        0,
        len(rows) - created,
    )

    return {
        "created":
            created,

        "skipped_existing":
            skipped_existing,
    }


# ============================================================
# DAILY CHANGES
# ============================================================

def calculate_daily_changes(
    db: Session,
):
    """
    Existing compatibility function.

    IMPORTANT:
    Large historical backfills do NOT automatically run
    this function anymore.

    Fund Health calculations derive returns directly from
    NAV history, so recalculating millions of stored
    daily-change columns after every backfill is unnecessary.
    """

    product_ids = (
        db.query(
            FundNAVHistory.product_id
        )
        .distinct()
        .all()
    )

    updated = 0

    for (
        product_id,
    ) in product_ids:

        rows = (
            db.query(
                FundNAVHistory
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

        previous_nav = None

        for row in rows:

            if (
                previous_nav is not None
                and previous_nav > 0
            ):

                daily_change = (
                    row.nav
                    - previous_nav
                )

                daily_change_percentage = (
                    daily_change
                    / previous_nav
                ) * 100

                row.daily_change = round(
                    daily_change,
                    4,
                )

                row.daily_change_percentage = (
                    round(
                        daily_change_percentage,
                        4,
                    )
                )

                updated += 1

            previous_nav = (
                row.nav
            )

    return updated


# ============================================================
# SYNC HISTORICAL NAV
# ============================================================

def sync_historical_nav(
    db: Session,
    months: int = 12,
    years: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    recalculate_daily_changes: bool = False,
):
    """
    Historical NAV synchronizer.

    Supports:

    - normal month-based syncing
    - exact multi-year historical backfill
    - explicit start/end dates for testing
    - safe reruns
    - resumable backfills
    - duplicate protection
    - one product-map query instead of millions
    - one commit per AMFI window

    Priority:

    explicit start_date
        >
    years
        >
    months
    """

    if end_date is None:

        end_date = date.today()

    if start_date is None:

        if (
            years is not None
            and years > 0
        ):

            start_date = (
                subtract_years(
                    end_date,
                    years,
                )
            )

        else:

            if months <= 0:

                raise ValueError(
                    "months must be greater "
                    "than zero."
                )

            start_date = (
                end_date
                - timedelta(
                    days=months * 30
                )
            )

    if start_date > end_date:

        raise ValueError(
            "start_date cannot be later "
            "than end_date."
        )

    print(
        "\n"
        "============================================"
    )

    print(
        "InvestiGenie Historical NAV Sync"
    )

    print(
        "============================================"
    )

    print(
        f"Start date : {start_date}"
    )

    print(
        f"End date   : {end_date}"
    )

    print(
        "Building AMFI product map..."
    )

    product_map = (
        build_product_map(
            db
        )
    )

    print(
        f"Mapped products: "
        f"{len(product_map)}"
    )

    total_days = (
        end_date
        - start_date
    ).days + 1

    estimated_windows = (
        (
            total_days
            + AMFI_WINDOW_DAYS
        )
        // (
            AMFI_WINDOW_DAYS
            + 1
        )
    )

    current_start = (
        start_date
    )

    total_created = 0

    total_existing = 0

    total_missing_products = 0

    total_records_received = 0

    total_prepared = 0

    windows_processed = 0

    try:

        while (
            current_start
            <= end_date
        ):

            current_end = min(
                current_start
                + timedelta(
                    days=AMFI_WINDOW_DAYS
                ),
                end_date,
            )

            window_number = (
                windows_processed + 1
            )

            print(
                "\n"
                f"[Window "
                f"{window_number}/"
                f"{estimated_windows}] "
                f"{current_start} "
                f"-> {current_end}"
            )

            # ---------------------------------------------
            # FETCH
            # ---------------------------------------------

            content = (
                fetch_amfi_history(
                    start_date=
                        current_start,

                    end_date=
                        current_end,
                )
            )

            # ---------------------------------------------
            # PARSE
            # ---------------------------------------------

            records = (
                parse_historical_records(
                    content
                )
            )

            received = (
                len(records)
            )

            total_records_received += (
                received
            )

            print(
                f"AMFI records received: "
                f"{received:,}"
            )

            # ---------------------------------------------
            # MAP PRODUCT IDs
            # ---------------------------------------------

            (
                prepared_rows,
                missing_products,
            ) = prepare_history_records(
                records=
                    records,

                product_map=
                    product_map,
            )

            prepared_count = (
                len(
                    prepared_rows
                )
            )

            total_prepared += (
                prepared_count
            )

            total_missing_products += (
                missing_products
            )

            # ---------------------------------------------
            # BULK INSERT
            # ---------------------------------------------

            result = (
                bulk_insert_history_records(
                    db=db,
                    rows=prepared_rows,
                )
            )

            created = (
                result["created"]
            )

            existing = (
                result[
                    "skipped_existing"
                ]
            )

            total_created += (
                created
            )

            total_existing += (
                existing
            )

            # Commit each window.
            db.commit()

            windows_processed += 1

            print(
                f"Prepared: "
                f"{prepared_count:,}"
            )

            print(
                f"Inserted: "
                f"{created:,}"
            )

            print(
                f"Already existed: "
                f"{existing:,}"
            )

            print(
                f"Missing product mappings: "
                f"{missing_products:,}"
            )

            print(
                f"Total new NAV rows: "
                f"{total_created:,}"
            )

            # ---------------------------------------------
            # NEXT WINDOW
            # ---------------------------------------------

            current_start = (
                current_end
                + timedelta(days=1)
            )

        # ==================================================
        # OPTIONAL DAILY CHANGE RECALCULATION
        # ==================================================

        daily_rows_updated = 0

        if recalculate_daily_changes:

            print(
                "\nRecalculating stored "
                "daily-change values..."
            )

            daily_rows_updated = (
                calculate_daily_changes(
                    db=db
                )
            )

            db.commit()

        result = {
            "start_date":
                start_date.isoformat(),

            "end_date":
                end_date.isoformat(),

            "months_requested":
                months,

            "years_requested":
                years,

            "windows_processed":
                windows_processed,

            "records_received":
                total_records_received,

            "records_prepared":
                total_prepared,

            "history_created":
                total_created,

            "existing_records_skipped":
                total_existing,

            "missing_products_skipped":
                total_missing_products,

            "daily_change_rows_updated":
                daily_rows_updated,

            "synced_at":
                datetime.utcnow().isoformat(),
        }

        print(
            "\n"
            "============================================"
        )

        print(
            "Historical NAV sync complete"
        )

        print(
            "============================================"
        )

        print(
            result
        )

        return result

    except Exception:

        db.rollback()

        print(
            "\nHistorical NAV sync FAILED."
        )

        print(
            "Completed windows remain safely "
            "committed and the process can be rerun."
        )

        raise
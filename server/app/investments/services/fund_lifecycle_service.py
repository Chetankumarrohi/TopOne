from __future__ import annotations

from datetime import (
    date,
    datetime,
)

from sqlalchemy.orm import Session

from app.investments.models.investment_product import (
    InvestmentProduct,
)

from app.investments.services.amfi_fund_master_service import (
    fetch_amfi_nav_file,
    parse_amfi_records,
)


# ============================================================
# LIFECYCLE CONSTANTS
# ============================================================

SCHEME_ACTIVE = "ACTIVE"
SCHEME_LEGACY = "LEGACY"
SCHEME_SEGREGATED = "SEGREGATED"
SCHEME_DEFUNCT = "DEFUNCT"
SCHEME_MERGED = "MERGED"
SCHEME_CLOSED = "CLOSED"
SCHEME_ZERO_NAV_REVIEW = "ZERO_NAV_REVIEW"


# A normal mutual-fund scheme should not remain without a
# refreshed NAV for long periods.
#
# We use a conservative threshold here so weekends,
# holidays and temporary AMFI delays do not misclassify funds.
STALE_LIVE_NAV_DAYS = 45


# ============================================================
# TEXT HELPERS
# ============================================================

def _normalize_text(
    value: str | None,
) -> str:

    return (
        str(
            value
            or ""
        )
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .strip()
    )


def _contains_any(
    text: str,
    terms: tuple[str, ...],
) -> bool:

    return any(
        term in text
        for term in terms
    )


# ============================================================
# NAME-BASED CLASSIFIERS
# ============================================================

SEGREGATED_TERMS = (
    "segregated portfolio",
    "seg portfolio",
    "seg. portfolio",
    "side pocket",
    "side-pocket",
)


DEFUNCT_TERMS = (
    "defunct",
    "wound up",
    "winding up",
    "terminated",
)


CLOSED_TERMS = (
    "scheme closed",
    "scheme matured",
    "matured scheme",
    "closed for subscription",
)


MERGED_TERMS = (
    "merged into",
    "merged with",
    "scheme merged",
)


LEGACY_TERMS = (
    "bonus option",
    "bonus plan",
)


# Close-ended schemes and target-maturity products can legitimately
# remain in the current AMFI file with an older last-reported NAV.
CLOSE_ENDED_CATEGORY_TERMS = (
    "close ended schemes",
    "closed ended schemes",
)

TARGET_MATURITY_NAME_TERMS = (
    "fixed term plan",
    "fixed maturity plan",
    " fmp ",
    "target maturity",
    "target date",
)


# ============================================================
# SINGLE PRODUCT CLASSIFICATION
# ============================================================

def classify_product_lifecycle(
    product: InvestmentProduct,
    *,
    seen_in_current_amfi: bool,
    amfi_category: str | None = None,
) -> tuple[
    str,
    str,
]:
    """
    Conservative lifecycle classifier.

    Important:
    It never fabricates NAVs and never deletes products.

    Returns:
        (scheme_status, lifecycle_reason)
    """

    name = _normalize_text(
        product.name
    )

    padded_name = f" {name} "

    normalized_amfi_category = (
        _normalize_text(
            amfi_category
        )
    )

    today = date.today()

    nav_age_days = None

    if product.nav_date:
        nav_age_days = (
            today
            - product.nav_date
        ).days

    nav_value = (
        product.nav
        if product.nav is not None
        else 0.0
    )

    # =====================================================
    # 0. NO AMFI SCHEME CODE
    # =====================================================

    if not product.scheme_code:
        return (
            SCHEME_LEGACY,
            (
                "Mutual-fund record has no AMFI scheme code "
                "and cannot be validated against the current "
                "AMFI master feed."
            ),
        )

    # =====================================================
    # 1. SEGREGATED / SIDE-POCKET
    # =====================================================

    if _contains_any(
        name,
        SEGREGATED_TERMS,
    ):
        return (
            SCHEME_SEGREGATED,
            (
                "Scheme name indicates a "
                "segregated / side-pocket portfolio."
            ),
        )

    # =====================================================
    # 2. EXPLICIT DEFUNCT
    # =====================================================

    if _contains_any(
        name,
        DEFUNCT_TERMS,
    ):
        return (
            SCHEME_DEFUNCT,
            (
                "Scheme name explicitly indicates "
                "a defunct / terminated product."
            ),
        )

    # =====================================================
    # 3. EXPLICIT MERGED
    # =====================================================

    if _contains_any(
        name,
        MERGED_TERMS,
    ):
        return (
            SCHEME_MERGED,
            (
                "Scheme name indicates that "
                "the scheme was merged."
            ),
        )

    # =====================================================
    # 4. EXPLICIT CLOSED / MATURED
    # =====================================================

    if _contains_any(
        name,
        CLOSED_TERMS,
    ):
        return (
            SCHEME_CLOSED,
            (
                "Scheme name indicates a "
                "closed or matured product."
            ),
        )

    # =====================================================
    # 5. ZERO NAV
    # =====================================================

    if nav_value <= 0:

        # A zero NAV appearing in AMFI still needs review.
        # We do not assume the scheme is dead merely because
        # its current NAV is zero.
        return (
            SCHEME_ZERO_NAV_REVIEW,
            (
                "Current NAV is zero or unavailable. "
                "Manual/source classification required "
                "before treating this scheme as investable."
            ),
        )

    # =====================================================
    # 6. OLD BONUS VARIANTS
    # =====================================================

    if (
        _contains_any(
            name,
            LEGACY_TERMS,
        )
        and nav_age_days is not None
        and nav_age_days
        > STALE_LIVE_NAV_DAYS
    ):
        return (
            SCHEME_LEGACY,
            (
                "Old Bonus-plan variant with "
                f"NAV last updated {nav_age_days} days ago."
            ),
        )

    # =====================================================
    # 7. NO LONGER PRESENT IN CURRENT AMFI FEED
    # =====================================================

    if not seen_in_current_amfi:

        return (
            SCHEME_LEGACY,
            (
                "Scheme is not present in the "
                "current AMFI NAV master feed."
            ),
        )

    # =====================================================
    # 8. CLOSE-ENDED / MATURITY-ORIENTED SCHEMES
    # =====================================================

    is_close_ended = (
        _contains_any(
            normalized_amfi_category,
            CLOSE_ENDED_CATEGORY_TERMS,
        )
    )

    is_maturity_oriented = (
        _contains_any(
            padded_name,
            TARGET_MATURITY_NAME_TERMS,
        )
    )

    if (
        seen_in_current_amfi
        and nav_value > 0
        and (
            is_close_ended
            or is_maturity_oriented
        )
    ):
        # Presence in AMFI alone does not prove that an old
        # close-ended / maturity-oriented scheme is currently
        # operating. AMFI can retain historical schemes long
        # after their last NAV.
        if (
            nav_age_days is not None
            and nav_age_days
            > STALE_LIVE_NAV_DAYS
        ):
            return (
                SCHEME_LEGACY,
                (
                    "Close-ended / maturity-oriented scheme "
                    "remains in the current AMFI feed, but its "
                    f"NAV has not refreshed for {nav_age_days} "
                    "days. It is retained as historical/legacy "
                    "rather than treated as currently investable."
                ),
            )

        return (
            SCHEME_ACTIVE,
            (
                "Close-ended / maturity-oriented scheme is "
                "present in the current AMFI feed with a "
                "recent valid NAV."
            ),
        )

    # =====================================================
    # 9. PRESENT IN AMFI BUT NAV IS VERY OLD
    # =====================================================

    if (
        nav_age_days is not None
        and nav_age_days
        > STALE_LIVE_NAV_DAYS
    ):
        return (
            SCHEME_LEGACY,
            (
                "Scheme remains in AMFI master data "
                "but NAV has not refreshed for "
                f"{nav_age_days} days."
            ),
        )

    # =====================================================
    # 10. CURRENT SCHEME
    # =====================================================

    return (
        SCHEME_ACTIVE,
        (
            "Scheme is present in the current "
            "AMFI feed with a valid recent NAV."
        ),
    )


# ============================================================
# APPLY STATUS
# ============================================================

def apply_lifecycle_status(
    product: InvestmentProduct,
    *,
    scheme_status: str,
    reason: str,
    seen_in_current_amfi: bool,
):

    now = datetime.utcnow()

    product.scheme_status = (
        scheme_status
    )

    product.lifecycle_reason = (
        reason
    )

    product.lifecycle_updated_at = (
        now
    )

    if seen_in_current_amfi:
        product.last_seen_in_amfi = (
            now
        )

    # =====================================================
    # INVESTMENT AVAILABILITY SAFETY
    # =====================================================

    if scheme_status in {
        SCHEME_LEGACY,
        SCHEME_SEGREGATED,
        SCHEME_DEFUNCT,
        SCHEME_MERGED,
        SCHEME_CLOSED,
        SCHEME_ZERO_NAV_REVIEW,
    }:

        product.purchase_allowed = (
            False
        )

        product.sip_allowed = (
            False
        )


# ============================================================
# ALL-FUND CLASSIFIER
# ============================================================

def classify_all_fund_lifecycles(
    db: Session,
    *,
    batch_size: int = 500,
):
    """
    Classify lifecycle state for all active mutual-fund records.

    Uses the current AMFI feed as the authoritative presence check.
    """

    content = (
        fetch_amfi_nav_file()
    )

    records = (
        parse_amfi_records(
            content
        )
    )

    current_amfi_records = {
        str(
            record["scheme_code"]
        ):
            record
        for record
        in records
    }

    current_amfi_codes = set(
        current_amfi_records.keys()
    )

    counts = {
        SCHEME_ACTIVE: 0,
        SCHEME_LEGACY: 0,
        SCHEME_SEGREGATED: 0,
        SCHEME_DEFUNCT: 0,
        SCHEME_MERGED: 0,
        SCHEME_CLOSED: 0,
        SCHEME_ZERO_NAV_REVIEW: 0,
    }

    processed = 0

    last_id = 0

    while True:

        products = (
            db.query(
                InvestmentProduct
            )
            .filter(
                InvestmentProduct.id
                > last_id,

                InvestmentProduct.product_type
                == "MUTUAL_FUND",
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

            processed += 1

            scheme_code = (
                str(
                    product.scheme_code
                )
                if product.scheme_code
                else None
            )

            seen_in_current_amfi = (
                scheme_code
                in current_amfi_codes
                if scheme_code
                else False
            )

            amfi_record = (
                current_amfi_records.get(
                    scheme_code
                )
                if scheme_code
                else None
            )

            amfi_category = (
                amfi_record.get(
                    "category"
                )
                if amfi_record
                else None
            )

            (
                scheme_status,
                reason,
            ) = classify_product_lifecycle(
                product,
                seen_in_current_amfi=
                    seen_in_current_amfi,
                amfi_category=
                    amfi_category,
            )

            apply_lifecycle_status(
                product,
                scheme_status=
                    scheme_status,
                reason=reason,
                seen_in_current_amfi=
                    seen_in_current_amfi,
            )

            counts[
                scheme_status
            ] += 1

            last_id = (
                product.id
            )

        db.commit()

        db.expunge_all()

    return {
        "processed":
            processed,

        "amfi_records":
            len(records),

        "status_counts":
            counts,

        "classified_at":
            datetime.utcnow()
            .isoformat(),
    }

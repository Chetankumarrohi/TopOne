from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
import re
from typing import Iterable

import requests
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.investments.models.investment_product import (
    InvestmentProduct,
)


# ============================================================
# OFFICIAL AMC FACTSHEET SOURCES
# ============================================================
#
# This first adapter supports Bajaj Finserv Mutual Fund.
# Add new AMC adapters to FACTSHEET_SOURCES as they are implemented.
#
# IMPORTANT:
# Keep these URLs on official AMC domains only.
# ============================================================

@dataclass(frozen=True)
class FactsheetSource:
    provider_key: str
    provider_aliases: tuple[str, ...]
    factsheet_url: str
    parser: str


FACTSHEET_SOURCES: tuple[FactsheetSource, ...] = (
    FactsheetSource(
        provider_key="BAJAJ_FINSERV",
        provider_aliases=(
            "bajaj finserv mutual fund",
            "bajaj finserv asset management",
            "bajaj finserv",
        ),
        # Official Bajaj Finserv AMC monthly factsheet.
        # This URL should be refreshed when a newer monthly factsheet
        # becomes available.
        factsheet_url=(
            "https://media.bajajamc.com/"
            "wp-content/uploads/2026/04/"
            "Bajaj-Finserv-Factsheet_April.pdf"
        ),
        parser="BAJAJ",
    ),
)


REQUEST_TIMEOUT = 90

FACTSHEET_CACHE_DIR = Path(
    "data/factsheet_cache"
)



# ============================================================
# NORMALIZATION
# ============================================================

def _clean_text(value: str | None) -> str:
    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def _normalize(value: str | None) -> str:
    return (
        _clean_text(value)
        .lower()
        .replace("&", " and ")
    )


def _safe_float(value):
    if value is None:
        return None

    text = (
        str(value)
        .replace(",", "")
        .replace("₹", "")
        .replace("rs.", "")
        .replace("rs", "")
        .replace("%", "")
        .strip()
    )

    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _safe_date(value: str | None):
    if not value:
        return None

    text = _clean_text(value)

    text = re.sub(
        r"(\d)(st|nd|rd|th)\b",
        r"\1",
        text,
        flags=re.IGNORECASE,
    )

    formats = (
        "%d %B %Y",
        "%d %b %Y",
        "%d %B, %Y",
        "%d %b, %Y",
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
    )

    for date_format in formats:
        try:
            return datetime.strptime(
                text,
                date_format,
            ).date()
        except ValueError:
            continue

    return None


def normalize_scheme_family_name(
    scheme_name: str,
) -> str:
    """
    Convert plan/option variants into the underlying scheme name.

    Example:
        BAJAJ FINSERV LARGE CAP FUND - DIRECT PLAN - GROWTH
        -> bajaj finserv large cap fund
    """

    text = _normalize(
        scheme_name
    )

    replacements = (
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
    )

    for pattern in replacements:
        text = re.sub(
            pattern,
            " ",
            text,
            flags=re.IGNORECASE,
        )

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def find_source_for_provider(
    provider: str | None,
):
    provider_text = _normalize(
        provider
    )

    for source in FACTSHEET_SOURCES:
        if any(
            alias in provider_text
            or provider_text in alias
            for alias in source.provider_aliases
            if provider_text
        ):
            return source

    return None


# ============================================================
# PDF FETCHING / TEXT EXTRACTION
# ============================================================

def fetch_pdf_bytes(
    url: str,
) -> bytes:
    """
    Download an official AMC factsheet with a local cache fallback.

    Behaviour:
    1. If a cached PDF exists, use it immediately.
    2. Otherwise download the official AMC PDF and cache it.
    3. If the network later fails but a cache exists, use the cache.
    4. If neither download nor cache is available, raise a clear error.
    """

    FACTSHEET_CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = (
        url.rstrip("/")
        .split("/")[-1]
        .split("?")[0]
    )

    if not filename.lower().endswith(
        ".pdf"
    ):
        filename = (
            f"factsheet_"
            f"{abs(hash(url))}.pdf"
        )

    cache_path = (
        FACTSHEET_CACHE_DIR
        / filename
    )

    # -----------------------------------------
    # Prefer local cache
    # -----------------------------------------

    if cache_path.exists():
        cached = (
            cache_path.read_bytes()
        )

        if cached:
            print(
                "Using cached factsheet:",
                cache_path,
            )

            return cached

    # -----------------------------------------
    # Download from official AMC source
    # -----------------------------------------

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent":
                    "InvestiGenie/1.0",
                "Accept":
                    "application/pdf,"
                    "application/octet-stream;q=0.9,"
                    "*/*;q=0.8",
            },
        )

        response.raise_for_status()

        pdf_bytes = (
            response.content
        )

        if not pdf_bytes:
            raise ValueError(
                "Factsheet response was empty."
            )

        # Lightweight PDF sanity check.
        if not pdf_bytes.startswith(
            b"%PDF"
        ):
            content_type = (
                response.headers.get(
                    "Content-Type",
                    "",
                )
            )

            raise ValueError(
                "Factsheet response did not "
                "look like a PDF. "
                f"Content-Type={content_type!r}"
            )

        cache_path.write_bytes(
            pdf_bytes
        )

        print(
            "Cached factsheet:",
            cache_path,
        )

        return pdf_bytes

    except (
        requests.RequestException,
        ValueError,
    ) as error:

        # -------------------------------------
        # Network failed: fall back to cache
        # -------------------------------------

        if cache_path.exists():
            cached = (
                cache_path.read_bytes()
            )

            if cached:
                print(
                    "Network unavailable; "
                    "using cached factsheet:",
                    cache_path,
                )

                return cached

        raise RuntimeError(
            "Could not download factsheet "
            f"from {url}: {error}"
        ) from error


def extract_pdf_pages(
    pdf_bytes: bytes,
):
    reader = PdfReader(
        BytesIO(pdf_bytes)
    )

    pages = []

    for index, page in enumerate(
        reader.pages
    ):
        text = (
            page.extract_text()
            or ""
        )

        pages.append(
            {
                "page_number":
                    index + 1,
                "text":
                    text,
            }
        )

    return pages


# ============================================================
# SCHEME PAGE MATCHING
# ============================================================

def find_scheme_page(
    pages,
    scheme_name: str,
):
    """
    Find the actual factsheet page for the underlying scheme.

    This deliberately avoids table-of-contents/index pages and requires
    the normalized scheme title to appear near the beginning of the page.
    """

    target = normalize_scheme_family_name(
        scheme_name
    )

    if not target:
        return None

    target_tokens = set(
        target.split()
    )

    metadata_markers = (
        "benchmark",
        "fund manager",
        "date of allotment",
        "aum",
        "expense ratio",
        "exit load",
        "investment objective",
        "portfolio",
        "riskometer",
        "minimum investment",
        "nav",
    )

    index_markers = (
        "page no.content",
        "page no. content",
        "table of contents",
        "contents",
        "index",
    )

    candidates = []

    for page in pages:
        raw_text = (
            page.get("text")
            or ""
        )

        page_text = _normalize(
            raw_text
        )

        if not page_text:
            continue

        searchable = re.sub(
            r"[^a-z0-9]+",
            " ",
            page_text,
        )

        searchable = re.sub(
            r"\s+",
            " ",
            searchable,
        ).strip()

        # Genuine scheme pages normally start with the fund title.
        first_chunk = searchable[:600]

        exact_anywhere = (
            target in searchable
        )

        exact_near_start = (
            target in first_chunk
        )

        page_tokens = set(
            searchable.split()
        )

        overlap = len(
            target_tokens
            & page_tokens
        )

        overlap_ratio = (
            overlap
            / len(target_tokens)
            if target_tokens
            else 0
        )

        if (
            not exact_anywhere
            and overlap_ratio < 0.8
        ):
            continue

        marker_count = sum(
            1
            for marker
            in metadata_markers
            if marker in page_text
        )

        index_count = sum(
            1
            for marker
            in index_markers
            if marker in page_text
        )

        many_scheme_mentions = (
            page_text.count(
                "bajaj finserv"
            )
        )

        score = 0.0

        if exact_near_start:
            score += 300
        elif exact_anywhere:
            score += 80

        score += (
            overlap_ratio
            * 40
        )

        score += (
            marker_count
            * 20
        )

        if marker_count >= 4:
            score += 80

        score -= (
            index_count
            * 150
        )

        if many_scheme_mentions > 8:
            score -= 250

        if len(searchable) < 900:
            score -= 60

        candidates.append(
            (
                score,
                exact_near_start,
                marker_count,
                page,
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2],
            -item[3]["page_number"],
        ),
        reverse=True,
    )

    best_score, starts_with_scheme, _, best_page = (
        candidates[0]
    )

    # Strict safety gate: never return a weak/index-page match.
    if (
        not starts_with_scheme
        or best_score < 300
    ):
        return None

    return best_page


# ============================================================
# GENERIC REGEX HELPERS
# ============================================================

def _first_match(
    text: str,
    patterns: Iterable[str],
):
    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        if match:
            return _clean_text(
                match.group(1)
            )

    return None


def _extract_percentage(
    text: str,
    label_patterns: Iterable[str],
):
    for label in label_patterns:
        pattern = (
            rf"{label}"
            r"\s*[:\-]?\s*"
            r"([0-9]+(?:\.[0-9]+)?)\s*%"
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return _safe_float(
                match.group(1)
            )

    return None


# ============================================================
# BAJAJ FINSERV FACTSHEET PARSER
# ============================================================

def parse_bajaj_scheme_page(
    text: str,
):
    """
    Parse the current Bajaj Finserv AMC factsheet layout.

    The PDF extraction is line-oriented, so this parser uses both
    labelled regexes and section-aware parsing. It is conservative:
    values are only returned when the source text clearly supports them.
    """

    raw = text or ""
    normalized = _clean_text(raw)

    # --------------------------------------------------------
    # INVESTMENT OBJECTIVE
    # --------------------------------------------------------

    investment_objective = _first_match(
        normalized,
        (
            r"((?:The objective|The investment objective)\s+.+?achieved\.)\s+INVESTMENT OBJECTIVE\b",
            r"((?:The objective|The investment objective)\s+.+?)\s+INVESTMENT OBJECTIVE\b",
        ),
    )

    # --------------------------------------------------------
    # FUND MANAGER
    # --------------------------------------------------------

    fund_manager = _first_match(
        normalized,
        (
            r"FUND MANAGER:\s*(.+?)(?=\s+DATE OF ALLOTMENT:)",
            r"FUND MANAGER:\s*(.+?)(?=\s+BENCHMARK:)",
        ),
    )

    # --------------------------------------------------------
    # DATE OF ALLOTMENT / LAUNCH DATE
    # --------------------------------------------------------

    allotment_raw = _first_match(
        normalized,
        (
            r"DATE OF ALLOTMENT:\s*([0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+[0-9]{4})",
            r"DATE OF ALLOTMENT:\s*([0-9]{1,2}[-/][A-Za-z0-9]+[-/][0-9]{2,4})",
        ),
    )

    # --------------------------------------------------------
    # BENCHMARK
    # --------------------------------------------------------

    benchmark = _first_match(
        normalized,
        (
            r"BENCHMARK:\s*(.+?)(?=\s*\*AUM\b)",
            r"BENCHMARK:\s*(.+?)(?=\s+FUND FEATURES\b)",
        ),
    )

    # --------------------------------------------------------
    # AUM
    # Current Bajaj layout:
    # *AUM (IN ` CRORE)
    # Month end AUM
    # AAUM
    # 1,362.68
    # 1,444.84
    # --------------------------------------------------------

    aum_raw = _first_match(
        normalized,
        (
            r"\*AUM\s*\(IN\s*[`₹]?\s*CRORE\)\s*Month end AUM\s*AAUM\s*([0-9,]+(?:\.[0-9]+)?)",
            r"Month end AUM\s*AAUM\s*([0-9,]+(?:\.[0-9]+)?)",
            r"Month end AUM\s*([0-9,]+(?:\.[0-9]+)?)",
        ),
    )

    # --------------------------------------------------------
    # EXIT LOAD
    # --------------------------------------------------------

    exit_load = _first_match(
        normalized,
        (
            r"Exit Load:\s*(.+?)(?=\s+SCHEME DETAILS\b)",
            r"Exit Load:\s*(.+?)(?=\s+TOTAL EXPENSE RATIO\b)",
        ),
    )

    # --------------------------------------------------------
    # TER
    # Current Bajaj layout:
    # TOTAL EXPENSE RATIO (TER)
    # Regular Plan
    # Direct Plan
    # Including Additional Expenses...
    # 2.11%
    # 0.61%
    # --------------------------------------------------------

    regular_ter = None
    direct_ter = None

    ter_match = re.search(
        r"TOTAL EXPENSE RATIO\s*\(TER\)\s*"
        r"Regular Plan\s*"
        r"Direct Plan\s*"
        r".{0,250}?"
        r"([0-9]+(?:\.[0-9]+)?)%\s*"
        r"([0-9]+(?:\.[0-9]+)?)%",
        normalized,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if ter_match:
        regular_ter = _safe_float(
            ter_match.group(1)
        )

        direct_ter = _safe_float(
            ter_match.group(2)
        )

    else:
        regular_ter = _safe_float(
            _first_match(
                normalized,
                (
                    r"Regular Plan.{0,220}?([0-9]+(?:\.[0-9]+)?)%",
                ),
            )
        )

        direct_ter = _safe_float(
            _first_match(
                normalized,
                (
                    r"Direct Plan.{0,220}?([0-9]+(?:\.[0-9]+)?)%",
                ),
            )
        )

    # --------------------------------------------------------
    # PORTFOLIO DATE
    # --------------------------------------------------------

    holdings_as_of_raw = _first_match(
        normalized,
        (
            r"PORTFOLIO\s*\(as on\s*([^)]+)\)",
        ),
    )

    holdings_as_of = _safe_date(
        holdings_as_of_raw
    )

    # --------------------------------------------------------
    # ASSET ALLOCATION
    #
    # Example:
    # COMPOSITION BY ASSET (%)
    # Net Equities Reverse Repo / TREPS & Net Current Assets
    # 97.82% 2.18%
    # --------------------------------------------------------

    equity_percentage = None
    debt_percentage = None
    cash_percentage = None

    asset_match = re.search(
        r"COMPOSITION BY ASSET\s*\(%\)\s*"
        r"Net Equities\s*"
        r"Reverse Repo\s*/\s*TREPS\s*&\s*Net Current Assets\s*"
        r"([0-9]+(?:\.[0-9]+)?)%\s*"
        r"([0-9]+(?:\.[0-9]+)?)%",
        normalized,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if asset_match:
        equity_percentage = _safe_float(
            asset_match.group(1)
        )

        cash_percentage = _safe_float(
            asset_match.group(2)
        )

        debt_percentage = 0.0

    else:
        # Secondary layout seen later in the same page.
        equity_percentage = _safe_float(
            _first_match(
                normalized,
                (
                    r"\bEquities\s+([0-9]+(?:\.[0-9]+)?)%",
                ),
            )
        )

        cash_percentage = _safe_float(
            _first_match(
                normalized,
                (
                    r"Cash\s*&\s*Cash Equivalent\s+([0-9]+(?:\.[0-9]+)?)%",
                    r"Cash\s+([0-9]+(?:\.[0-9]+)?)%",
                ),
            )
        )

    # --------------------------------------------------------
    # MARKET-CAP ALLOCATION
    #
    # Current Bajaj extraction can be:
    # Market Cap Allocation*
    # Large Cap
    # Mid Cap
    # *Data rebased to 100
    # 96.86%
    # 3.14%
    #
    # or include Small Cap as a third bucket.
    # --------------------------------------------------------

    large_cap_percentage = None
    mid_cap_percentage = None
    small_cap_percentage = None

    market_section_match = re.search(
        r"Market Cap Allocation\*?\s*"
        r"(.+?)"
        r"(?=\s*(?:COMPOSITION BY|Portfolio Turnover|$))",
        normalized,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if market_section_match:
        market_section = (
            market_section_match.group(1)
        )

        labels = []

        if re.search(
            r"\bLarge Cap\b",
            market_section,
            flags=re.IGNORECASE,
        ):
            labels.append(
                "large"
            )

        if re.search(
            r"\bMid Cap\b",
            market_section,
            flags=re.IGNORECASE,
        ):
            labels.append(
                "mid"
            )

        if re.search(
            r"\bSmall Cap\b",
            market_section,
            flags=re.IGNORECASE,
        ):
            labels.append(
                "small"
            )

        values = [
            _safe_float(value)
            for value in re.findall(
                r"([0-9]+(?:\.[0-9]+)?)%",
                market_section,
            )
        ]

        # Keep only enough values for the detected bucket labels.
        if (
            labels
            and len(values) >= len(labels)
        ):
            values = values[
                -len(labels):
            ]

            mapping = dict(
                zip(
                    labels,
                    values,
                )
            )

            large_cap_percentage = (
                mapping.get(
                    "large"
                )
            )

            mid_cap_percentage = (
                mapping.get(
                    "mid"
                )
            )

            small_cap_percentage = (
                mapping.get(
                    "small"
                )
            )

            # If Large + Mid explicitly exhaust the rebased allocation,
            # Small Cap is safely zero for that disclosed market-cap mix.
            if (
                "large" in mapping
                and "mid" in mapping
                and "small" not in mapping
            ):
                total = (
                    mapping["large"]
                    + mapping["mid"]
                )

                if abs(
                    total - 100.0
                ) <= 0.05:
                    small_cap_percentage = 0.0

    return {
        "benchmark":
            benchmark,

        "launch_date":
            _safe_date(
                allotment_raw
            ),

        "fund_manager":
            fund_manager,

        "investment_objective":
            investment_objective,

        "aum":
            _safe_float(
                aum_raw
            ),

        "regular_ter":
            regular_ter,

        "direct_ter":
            direct_ter,

        "exit_load":
            exit_load,

        "holdings_as_of":
            holdings_as_of,

        "equity_percentage":
            equity_percentage,

        "debt_percentage":
            debt_percentage,

        "cash_percentage":
            cash_percentage,

        "large_cap_percentage":
            large_cap_percentage,

        "mid_cap_percentage":
            mid_cap_percentage,

        "small_cap_percentage":
            small_cap_percentage,
    }


# ============================================================
# APPLY METADATA TO DATABASE
# ============================================================

def apply_factsheet_metadata(
    product: InvestmentProduct,
    metadata: dict,
):
    updated = []

    def assign(
        field: str,
        value,
    ):
        if value is None:
            return

        setattr(
            product,
            field,
            value,
        )

        updated.append(
            field
        )

    assign(
        "benchmark",
        metadata.get(
            "benchmark"
        ),
    )

    assign(
        "launch_date",
        metadata.get(
            "launch_date"
        ),
    )

    assign(
        "fund_manager",
        metadata.get(
            "fund_manager"
        ),
    )

    assign(
        "investment_objective",
        metadata.get(
            "investment_objective"
        ),
    )

    assign(
        "aum",
        metadata.get(
            "aum"
        ),
    )

    assign(
        "exit_load",
        metadata.get(
            "exit_load"
        ),
    )

    assign(
        "equity_percentage",
        metadata.get(
            "equity_percentage"
        ),
    )

    assign(
        "debt_percentage",
        metadata.get(
            "debt_percentage"
        ),
    )

    assign(
        "cash_percentage",
        metadata.get(
            "cash_percentage"
        ),
    )

    assign(
        "holdings_as_of",
        metadata.get(
            "holdings_as_of"
        ),
    )

    assign(
        "large_cap_percentage",
        metadata.get(
            "large_cap_percentage"
        ),
    )

    assign(
        "mid_cap_percentage",
        metadata.get(
            "mid_cap_percentage"
        ),
    )

    assign(
        "small_cap_percentage",
        metadata.get(
            "small_cap_percentage"
        ),
    )

    # Choose plan-specific TER.
    plan_type = (
        str(
            product.plan_type
            or ""
        )
        .strip()
        .upper()
    )

    if plan_type == "DIRECT":
        expense_ratio = (
            metadata.get(
                "direct_ter"
            )
        )

    elif plan_type == "REGULAR":
        expense_ratio = (
            metadata.get(
                "regular_ter"
            )
        )

    else:
        expense_ratio = (
            metadata.get(
                "direct_ter"
            )
            or metadata.get(
                "regular_ter"
            )
        )

    if expense_ratio is not None:
        product.expense_ratio = (
            expense_ratio
        )

        updated.append(
            "expense_ratio"
        )

    # IMPORTANT:
    # Do not derive asset-level equity exposure from Large/Mid/Small
    # market-cap buckets. Bajaj reports market-cap allocation rebased
    # to 100, while COMPOSITION BY ASSET reports the real equity/cash
    # exposure. The parser already maps that authoritative asset mix.

    product.data_updated_at = (
        datetime.utcnow()
    )

    return updated


# ============================================================
# PROVIDER SYNC
# ============================================================

def sync_provider_factsheet_metadata(
    db: Session,
    provider_key: str,
):
    source = next(
        (
            item
            for item
            in FACTSHEET_SOURCES
            if item.provider_key
            == provider_key
        ),
        None,
    )

    if source is None:
        raise ValueError(
            "Unsupported provider key: "
            f"{provider_key}"
        )

    pdf_bytes = fetch_pdf_bytes(
        source.factsheet_url
    )

    pages = extract_pdf_pages(
        pdf_bytes
    )

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

    provider_products = [
        product
        for product
        in products
        if (
            find_source_for_provider(
                product.provider
            )
            == source
        )
    ]

    processed = 0
    matched = 0
    updated = 0
    unmatched = 0
    field_counts = {}

    for product in provider_products:
        processed += 1

        page = find_scheme_page(
            pages=pages,
            scheme_name=product.name,
        )

        if page is None:
            unmatched += 1
            continue

        matched += 1

        if source.parser == "BAJAJ":
            metadata = (
                parse_bajaj_scheme_page(
                    page["text"]
                )
            )
        else:
            metadata = {}

        updated_fields = (
            apply_factsheet_metadata(
                product=product,
                metadata=metadata,
            )
        )

        if updated_fields:
            updated += 1

        for field in updated_fields:
            field_counts[field] = (
                field_counts.get(
                    field,
                    0,
                )
                + 1
            )

    db.commit()

    return {
        "provider":
            source.provider_key,

        "factsheet_url":
            source.factsheet_url,

        "processed":
            processed,

        "matched":
            matched,

        "updated":
            updated,

        "unmatched":
            unmatched,

        "fields_updated":
            field_counts,

        "synced_at":
            datetime.utcnow()
            .isoformat(),
    }


def sync_bajaj_factsheet_metadata(
    db: Session,
):
    return (
        sync_provider_factsheet_metadata(
            db=db,
            provider_key="BAJAJ_FINSERV",
        )
    )

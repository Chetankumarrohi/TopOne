from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

import requests


logger = logging.getLogger(__name__)


AMFI_FEED_URLS = (
    "https://www.amfiindia.com/spages/NAVAll.txt",
    "https://portal.amfiindia.com/spages/NAVAll.txt",
)

AMFI_CONNECT_TIMEOUT_SECONDS = 20
AMFI_READ_TIMEOUT_SECONDS = 60
AMFI_MAX_ATTEMPTS = 3
AMFI_RETRY_BACKOFF_SECONDS = (5, 15)

# Long enough for MASTER_SYNC -> NAV_SYNC in one pipeline run,
# short enough not to turn the cache into a persistent stale-data source.
AMFI_CACHE_TTL_SECONDS = 300


@dataclass(frozen=True)
class AmfiFeedSnapshot:
    content: str
    source_url: str
    fetched_monotonic: float


_cache_lock = threading.Lock()
_cached_snapshot: AmfiFeedSnapshot | None = None


def _validate_amfi_payload(content: str) -> None:
    if not content or not content.strip():
        raise requests.exceptions.ConnectionError(
            "AMFI NAV response was empty."
        )

    first_line = content.lstrip("\ufeff\r\n ").splitlines()[0]

    if (
        "Scheme Code" not in first_line
        or "Scheme Name" not in first_line
        or "Net Asset Value" not in first_line
    ):
        raise requests.exceptions.ConnectionError(
            "AMFI NAV response did not contain the expected header."
        )


def _is_retryable_http_status(status_code: int | None) -> bool:
    return (
        status_code == 429
        or (
            status_code is not None
            and 500 <= status_code <= 599
        )
    )


def _fetch_url(url: str) -> str:
    response = requests.get(
        url,
        timeout=(
            AMFI_CONNECT_TIMEOUT_SECONDS,
            AMFI_READ_TIMEOUT_SECONDS,
        ),
        headers={
            "User-Agent": "TopOne/1.0",
        },
        # We want explicit control over www -> portal fallback.
        allow_redirects=False,
    )

    # AMFI may redirect www to portal. Treat that as a signal to try
    # the explicit fallback URL rather than following a hidden chain.
    if 300 <= response.status_code <= 399:
        raise requests.exceptions.ConnectionError(
            f"AMFI endpoint redirected with HTTP "
            f"{response.status_code}."
        )

    if _is_retryable_http_status(response.status_code):
        raise requests.exceptions.HTTPError(
            f"Retryable AMFI HTTP status "
            f"{response.status_code}",
            response=response,
        )

    response.raise_for_status()

    content = response.text
    _validate_amfi_payload(content)

    return content


def fetch_amfi_feed() -> AmfiFeedSnapshot:
    """
    Fetch the AMFI NAVAll feed.

    Each attempt tries both official endpoint variants. If neither works,
    the service backs off before the next attempt. The final exception is
    propagated to the caller so the daily pipeline can fail safely.
    """

    last_error: Exception | None = None

    for attempt in range(
        1,
        AMFI_MAX_ATTEMPTS + 1,
    ):
        for url in AMFI_FEED_URLS:
            try:
                logger.info(
                    "Fetching AMFI feed from %s "
                    "(attempt %s/%s).",
                    url,
                    attempt,
                    AMFI_MAX_ATTEMPTS,
                )

                content = _fetch_url(url)

                logger.info(
                    "AMFI feed fetched successfully from %s.",
                    url,
                )

                return AmfiFeedSnapshot(
                    content=content,
                    source_url=url,
                    fetched_monotonic=time.monotonic(),
                )

            except (
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
            ) as error:
                last_error = error

                logger.warning(
                    "AMFI endpoint failed: %s | %s",
                    url,
                    error,
                )

            except requests.exceptions.HTTPError as error:
                status_code = (
                    error.response.status_code
                    if error.response is not None
                    else None
                )

                if not _is_retryable_http_status(status_code):
                    raise

                last_error = error

                logger.warning(
                    "AMFI endpoint returned retryable HTTP "
                    "status: %s | %s",
                    url,
                    error,
                )

        if attempt >= AMFI_MAX_ATTEMPTS:
            break

        delay = AMFI_RETRY_BACKOFF_SECONDS[
            attempt - 1
        ]

        logger.warning(
            "All AMFI endpoints failed on attempt %s/%s. "
            "Retrying in %s seconds.",
            attempt,
            AMFI_MAX_ATTEMPTS,
            delay,
        )

        time.sleep(delay)

    if last_error is not None:
        raise last_error

    raise RuntimeError(
        "AMFI feed fetch failed without an exception."
    )


def get_amfi_feed(
    *,
    force_refresh: bool = False,
) -> AmfiFeedSnapshot:
    """
    Return a recent in-process AMFI snapshot.

    MASTER_SYNC fetches the feed first. NAV_SYNC immediately afterward
    reuses that same payload instead of downloading NAVAll.txt again.
    """

    global _cached_snapshot

    with _cache_lock:
        if (
            not force_refresh
            and _cached_snapshot is not None
        ):
            age_seconds = (
                time.monotonic()
                - _cached_snapshot.fetched_monotonic
            )

            if age_seconds <= AMFI_CACHE_TTL_SECONDS:
                logger.info(
                    "Reusing cached AMFI feed "
                    "(age %.2f seconds).",
                    age_seconds,
                )
                return _cached_snapshot

        snapshot = fetch_amfi_feed()
        _cached_snapshot = snapshot
        return snapshot


def clear_amfi_feed_cache() -> None:
    global _cached_snapshot

    with _cache_lock:
        _cached_snapshot = None

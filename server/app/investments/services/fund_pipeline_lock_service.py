from __future__ import annotations

import os
import socket
import uuid

from datetime import (
    datetime,
    timedelta,
)

from sqlalchemy.exc import (
    IntegrityError,
)

from sqlalchemy.orm import Session

from app.investments.models.fund_pipeline_lock import (
    FundPipelineLock,
)


DAILY_FUND_PIPELINE_LOCK = (
    "DAILY_FUND_PIPELINE"
)


# The pipeline currently takes only a few minutes,
# but use a conservative expiry so an abandoned
# lock can recover automatically after a crash.
PIPELINE_LOCK_TTL_MINUTES = 180


def _utc_now() -> datetime:
    return datetime.utcnow()


def generate_lock_owner() -> str:
    """
    Generate a unique identifier for this
    pipeline execution/process.
    """

    hostname = socket.gethostname()
    pid = os.getpid()

    token = uuid.uuid4().hex[:12]

    return (
        f"{hostname}:"
        f"{pid}:"
        f"{token}"
    )


def acquire_pipeline_lock(
    db: Session,
    *,
    lock_name: str = (
        DAILY_FUND_PIPELINE_LOCK
    ),
    owner: str,
    ttl_minutes: int = (
        PIPELINE_LOCK_TTL_MINUTES
    ),
) -> bool:
    """
    Attempt to acquire a logical database lock.

    Returns True when this caller owns the lock.

    Returns False when another non-expired caller
    already owns it.
    """

    now = _utc_now()

    expires_at = (
        now
        + timedelta(
            minutes=ttl_minutes
        )
    )

    # -----------------------------------------------------
    # TRY EXISTING LOCK
    # -----------------------------------------------------

    existing = (
        db.query(
            FundPipelineLock
        )
        .filter(
            FundPipelineLock.lock_name
            == lock_name
        )
        .first()
    )

    if existing is not None:

        lock_expired = (
            existing.expires_at is None
            or existing.expires_at
            <= now
        )

        same_owner = (
            existing.owner
            == owner
        )

        if (
            not lock_expired
            and not same_owner
        ):
            return False

        # Existing lock is expired, or is being
        # renewed by the same owner.
        existing.owner = owner

        existing.acquired_at = (
            now
        )

        existing.expires_at = (
            expires_at
        )

        db.commit()

        return True

    # -----------------------------------------------------
    # CREATE FIRST LOCK ROW
    # -----------------------------------------------------

    lock = FundPipelineLock(
        lock_name=lock_name,
        owner=owner,
        acquired_at=now,
        expires_at=expires_at,
    )

    db.add(
        lock
    )

    try:
        db.commit()

        return True

    except IntegrityError:
        # Another process may have inserted the
        # unique lock row between SELECT and INSERT.
        db.rollback()

        return False


def release_pipeline_lock(
    db: Session,
    *,
    lock_name: str = (
        DAILY_FUND_PIPELINE_LOCK
    ),
    owner: str,
) -> bool:
    """
    Release the lock only when this execution
    is the current owner.

    Returns True if released.
    """

    lock = (
        db.query(
            FundPipelineLock
        )
        .filter(
            FundPipelineLock.lock_name
            == lock_name
        )
        .first()
    )

    if lock is None:
        return False

    if lock.owner != owner:
        return False

    lock.owner = None
    lock.acquired_at = None
    lock.expires_at = None

    db.commit()

    return True


def get_pipeline_lock_status(
    db: Session,
    *,
    lock_name: str = (
        DAILY_FUND_PIPELINE_LOCK
    ),
) -> dict:

    lock = (
        db.query(
            FundPipelineLock
        )
        .filter(
            FundPipelineLock.lock_name
            == lock_name
        )
        .first()
    )

    if lock is None:
        return {
            "lock_name":
                lock_name,

            "locked":
                False,

            "owner":
                None,

            "acquired_at":
                None,

            "expires_at":
                None,
        }

    now = _utc_now()

    locked = (
        lock.owner is not None
        and lock.expires_at
        is not None
        and lock.expires_at
        > now
    )

    return {
        "lock_name":
            lock_name,

        "locked":
            locked,

        "owner":
            lock.owner,

        "acquired_at": (
            lock.acquired_at.isoformat()
            if lock.acquired_at
            else None
        ),

        "expires_at": (
            lock.expires_at.isoformat()
            if lock.expires_at
            else None
        ),
    }
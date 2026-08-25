from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.investments.services.fund_pipeline_status_service import (
    get_pipeline_status,
)


def _utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def detect_pipeline_incident(
    db: Session,
) -> dict[str, Any]:
    """
    Inspect the complete fund-pipeline operational state
    and determine whether an actionable incident exists.

    Incident levels:
        NONE
        WARNING
        CRITICAL
    """

    status = get_pipeline_status(
        db=db
    )

    overall_status = (
        status.get(
            "overall_status",
            "CRITICAL",
        )
        or "CRITICAL"
    ).upper()

    pipeline = (
        status.get("pipeline")
        or {}
    )

    scheduler = (
        status.get("scheduler")
        or {}
    )

    lock = (
        status.get("lock")
        or {}
    )

    amfi = (
        status.get("amfi_freshness")
        or {}
    )

    summary = (
        status.get("summary")
        or {}
    )

    incidents: list[
        dict[str, Any]
    ] = []

    # ========================================================
    # PIPELINE FAILURES
    # ========================================================

    latest_run = (
        pipeline.get("latest_run")
        or {}
    )

    latest_run_status = (
        latest_run.get("status")
    )

    consecutive_failures = int(
        pipeline.get(
            "consecutive_failures",
            0,
        )
        or 0
    )

    if latest_run_status == "FAILED":
        incidents.append(
            {
                "code":
                    "PIPELINE_FAILED",

                "severity":
                    (
                        "CRITICAL"
                        if consecutive_failures >= 3
                        else "WARNING"
                    ),

                "message":
                    (
                        "Latest daily fund pipeline "
                        "execution failed."
                    ),

                "failed_step":
                    latest_run.get(
                        "failed_step"
                    ),

                "pipeline_run_id":
                    latest_run.get(
                        "id"
                    ),
            }
        )

    if consecutive_failures >= 3:
        incidents.append(
            {
                "code":
                    "REPEATED_PIPELINE_FAILURE",

                "severity":
                    "CRITICAL",

                "message":
                    (
                        "Three or more consecutive "
                        "pipeline failures detected."
                    ),

                "consecutive_failures":
                    consecutive_failures,
            }
        )

    # ========================================================
    # AMFI FRESHNESS
    # ========================================================

    amfi_status = (
        amfi.get(
            "status",
            "CRITICAL",
        )
        or "CRITICAL"
    ).upper()

    if amfi_status == "WARNING":
        incidents.append(
            {
                "code":
                    "AMFI_DATA_STALE",

                "severity":
                    "WARNING",

                "message":
                    (
                        "AMFI NAV data is outside the "
                        "normal freshness window."
                    ),

                "latest_nav_date":
                    amfi.get(
                        "latest_nav_date"
                    ),

                "nav_age_days":
                    amfi.get(
                        "nav_age_days"
                    ),
            }
        )

    elif amfi_status == "CRITICAL":
        incidents.append(
            {
                "code":
                    "AMFI_DATA_CRITICALLY_STALE",

                "severity":
                    "CRITICAL",

                "message":
                    (
                        "AMFI NAV data is critically "
                        "stale or unavailable."
                    ),

                "latest_nav_date":
                    amfi.get(
                        "latest_nav_date"
                    ),

                "nav_age_days":
                    amfi.get(
                        "nav_age_days"
                    ),
            }
        )

    # ========================================================
    # SCHEDULER
    # ========================================================

    scheduler_running = bool(
        scheduler.get(
            "running"
        )
    )

    if not scheduler_running:
        incidents.append(
            {
                "code":
                    "SCHEDULER_STOPPED",

                "severity":
                    "WARNING",

                "message":
                    (
                        "Daily fund pipeline scheduler "
                        "is not running."
                    ),
            }
        )

    # ========================================================
    # PIPELINE LOCK
    # ========================================================

    lock_held = bool(
        lock.get(
            "locked"
        )
    )

    # A normal held lock is not an incident.
    # The lock service already has expiry information,
    # which we will use later for stale-lock detection.

    # ========================================================
    # INCIDENT SEVERITY
    # ========================================================

    has_critical = any(
        incident.get("severity")
        == "CRITICAL"
        for incident in incidents
    )

    has_warning = any(
        incident.get("severity")
        == "WARNING"
        for incident in incidents
    )

    if has_critical:
        incident_level = "CRITICAL"

    elif has_warning:
        incident_level = "WARNING"

    else:
        incident_level = "NONE"

    return {
        "incident_active":
            bool(incidents),

        "incident_level":
            incident_level,

        "incident_count":
            len(incidents),

        "incidents":
            incidents,

        "overall_status":
            overall_status,

        "summary":
            {
                "pipeline_health":
                    summary.get(
                        "pipeline_health"
                    ),

                "amfi_status":
                    summary.get(
                        "amfi_status"
                    ),

                "scheduler_running":
                    scheduler_running,

                "pipeline_locked":
                    lock_held,

                "latest_run_status":
                    summary.get(
                        "latest_run_status"
                    ),

                "consecutive_failures":
                    consecutive_failures,
            },

        "checked_at":
            _utc_now_iso(),
    }
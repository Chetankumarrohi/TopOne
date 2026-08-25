from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.investments.services.fund_pipeline_health_service import (
    get_pipeline_health,
)

from app.investments.services.fund_pipeline_lock_service import (
    get_pipeline_lock_status,
)

from app.investments.services.fund_scheduler_service import (
    get_fund_scheduler_status,
)

from app.investments.services.amfi_freshness_service import (
    get_amfi_freshness_status,
)


def get_pipeline_status(
    db: Session,
) -> dict[str, Any]:
    """
    Return a complete operational status view for the
    daily InvestiGenie mutual-fund data pipeline.

    Combines:
    - pipeline audit health
    - scheduler state
    - database execution lock
    - AMFI NAV freshness
    """

    # ========================================================
    # PIPELINE HEALTH
    # ========================================================

    pipeline_health = (
        get_pipeline_health(
            db=db
        )
    )

    # ========================================================
    # DATABASE LOCK
    # ========================================================

    lock_status = (
        get_pipeline_lock_status(
            db
        )
    )

    # ========================================================
    # SCHEDULER
    # ========================================================

    scheduler_status = (
        get_fund_scheduler_status()
    )

    # ========================================================
    # AMFI DATA FRESHNESS
    # ========================================================

    amfi_freshness = (
        get_amfi_freshness_status(
            db=db
        )
    )

    # ========================================================
    # NORMALIZE STATES
    # ========================================================

    health_status = (
        pipeline_health.get(
            "health_status"
        )
    )

    amfi_status = (
        amfi_freshness.get(
            "status"
        )
    )

    scheduler_running = bool(
        scheduler_status.get(
            "running"
        )
    )

    lock_held = bool(
        lock_status.get(
            "locked"
        )
    )

    # ========================================================
    # OVERALL OPERATIONAL STATUS
    # ========================================================

    if (
        health_status == "CRITICAL"
        or amfi_status == "CRITICAL"
    ):
        overall_status = (
            "CRITICAL"
        )

    elif (
        health_status == "WARNING"
        or amfi_status == "WARNING"
        or not scheduler_running
    ):
        overall_status = (
            "WARNING"
        )

    else:
        overall_status = (
            "HEALTHY"
        )

    # ========================================================
    # OPERATIONAL REASONS
    # ========================================================

    reasons = []

    reasons.extend(
        pipeline_health.get(
            "reasons",
            [],
        )
        or []
    )

    reasons.extend(
        amfi_freshness.get(
            "reasons",
            [],
        )
        or []
    )

    if not scheduler_running:
        reasons.append(
            "Daily fund scheduler is not running."
        )

    # A held lock is not itself unhealthy.
    # It may simply mean the pipeline is currently executing.
    if lock_held:
        reasons.append(
            "Daily fund pipeline execution lock "
            "is currently held."
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "overall_status":
            overall_status,

        "reasons":
            reasons,

        "pipeline":
            pipeline_health,

        "scheduler":
            scheduler_status,

        "lock":
            lock_status,

        "amfi_freshness":
            amfi_freshness,

        "summary":
            {
                "pipeline_health":
                    health_status,

                "scheduler_running":
                    scheduler_running,

                "pipeline_locked":
                    lock_held,

                "amfi_status":
                    amfi_status,

                "latest_nav_date":
                    amfi_freshness.get(
                        "latest_nav_date"
                    ),

                "nav_age_days":
                    amfi_freshness.get(
                        "nav_age_days"
                    ),

                "latest_run_status":
                    (
                        (
                            pipeline_health.get(
                                "latest_run"
                            )
                            or {}
                        ).get(
                            "status"
                        )
                    ),

                "latest_run_id":
                    (
                        (
                            pipeline_health.get(
                                "latest_run"
                            )
                            or {}
                        ).get(
                            "id"
                        )
                    ),

                "consecutive_failures":
                    pipeline_health.get(
                        "consecutive_failures"
                    ),

                "hours_since_last_success":
                    pipeline_health.get(
                        "hours_since_last_success"
                    ),

                "next_scheduled_run":
                    scheduler_status.get(
                        "next_run_time"
                    ),
            },
    }
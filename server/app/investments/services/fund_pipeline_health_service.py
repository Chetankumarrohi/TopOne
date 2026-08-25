from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.investments.models.fund_pipeline_run import (
    FundPipelineRun,
)


PIPELINE_NAME = "DAILY_FUND_PIPELINE"

HEALTHY_MAX_AGE_HOURS = 30
WARNING_MAX_AGE_HOURS = 48

CONSECUTIVE_FAILURE_WARNING = 1
CONSECUTIVE_FAILURE_CRITICAL = 3


def _utc_now_db() -> datetime:
    """
    Return naive UTC datetime compatible with the
    current SQLite/SQLAlchemy DateTime columns.
    """

    return datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


def _serialize_run(
    run: FundPipelineRun | None,
) -> dict[str, Any] | None:
    if run is None:
        return None

    return {
        "id":
            run.id,

        "pipeline_name":
            run.pipeline_name,

        "status":
            run.status,

        "started_at":
            (
                run.started_at.isoformat()
                if run.started_at
                else None
            ),

        "finished_at":
            (
                run.finished_at.isoformat()
                if run.finished_at
                else None
            ),

        "duration_seconds":
            run.duration_seconds,

        "failed_step":
            run.failed_step,

        "error_message":
            run.error_message,
    }


def get_latest_pipeline_run(
    db: Session,
) -> FundPipelineRun | None:
    """
    Return the most recent daily fund pipeline run.
    """

    return (
        db.query(
            FundPipelineRun
        )
        .filter(
            FundPipelineRun.pipeline_name
            == PIPELINE_NAME
        )
        .order_by(
            FundPipelineRun.id.desc()
        )
        .first()
    )


def get_last_successful_pipeline_run(
    db: Session,
) -> FundPipelineRun | None:
    """
    Return the latest successful daily pipeline run.
    """

    return (
        db.query(
            FundPipelineRun
        )
        .filter(
            FundPipelineRun.pipeline_name
            == PIPELINE_NAME,

            FundPipelineRun.status
            == "SUCCESS",
        )
        .order_by(
            FundPipelineRun.id.desc()
        )
        .first()
    )


def get_recent_pipeline_runs(
    db: Session,
    limit: int = 10,
) -> list[FundPipelineRun]:
    """
    Return recent pipeline runs ordered newest first.
    """

    limit = max(
        1,
        min(
            int(limit),
            100,
        ),
    )

    return (
        db.query(
            FundPipelineRun
        )
        .filter(
            FundPipelineRun.pipeline_name
            == PIPELINE_NAME
        )
        .order_by(
            FundPipelineRun.id.desc()
        )
        .limit(
            limit
        )
        .all()
    )


def count_consecutive_failures(
    db: Session,
    max_runs: int = 20,
) -> int:
    """
    Count consecutive non-successful completed runs,
    starting from the most recent run.

    RUNNING and SKIPPED_LOCKED are not considered
    completed pipeline failures.
    """

    runs = get_recent_pipeline_runs(
        db=db,
        limit=max_runs,
    )

    failures = 0

    for run in runs:

        status = (
            str(
                run.status
                or ""
            )
            .upper()
            .strip()
        )

        if status == "SUCCESS":
            break

        if status in {
            "FAILED",
            "CRITICAL",
        }:
            failures += 1

        elif status in {
            "RUNNING",
            "SKIPPED_LOCKED",
        }:
            continue

        else:
            break

    return failures


def calculate_success_age_hours(
    run: FundPipelineRun | None,
) -> float | None:
    """
    Return hours elapsed since the latest successful
    pipeline finished.
    """

    if (
        run is None
        or run.finished_at is None
    ):
        return None

    elapsed = (
        _utc_now_db()
        - run.finished_at
    )

    return round(
        elapsed.total_seconds()
        / 3600,
        2,
    )


def determine_pipeline_health(
    *,
    latest_run: FundPipelineRun | None,
    last_success: FundPipelineRun | None,
    consecutive_failures: int,
    success_age_hours: float | None,
) -> tuple[str, list[str]]:
    """
    Determine the operational state of the data pipeline.

    Returns:
        (status, reasons)

    status:
        HEALTHY
        WARNING
        CRITICAL
    """

    reasons = []

    if latest_run is None:
        return (
            "CRITICAL",
            [
                "No daily fund pipeline run "
                "has been recorded."
            ],
        )

    latest_status = (
        str(
            latest_run.status
            or ""
        )
        .upper()
        .strip()
    )

    if (
        consecutive_failures
        >= CONSECUTIVE_FAILURE_CRITICAL
    ):
        reasons.append(
            "Multiple consecutive pipeline "
            "failures detected."
        )

    if last_success is None:
        reasons.append(
            "No successful daily fund pipeline "
            "run has been recorded."
        )

    if (
        success_age_hours is not None
        and success_age_hours
        > WARNING_MAX_AGE_HOURS
    ):
        reasons.append(
            "Last successful pipeline run is "
            "more than 48 hours old."
        )

    if (
        latest_status == "CRITICAL"
    ):
        reasons.append(
            "Latest pipeline run completed with "
            "critical validation issues."
        )

    if (
        consecutive_failures
        >= CONSECUTIVE_FAILURE_CRITICAL
        or last_success is None
        or (
            success_age_hours is not None
            and success_age_hours
            > WARNING_MAX_AGE_HOURS
        )
    ):
        return (
            "CRITICAL",
            reasons,
        )

    if (
        latest_status == "FAILED"
    ):
        reasons.append(
            "Latest pipeline execution failed."
        )

    if (
        consecutive_failures
        >= CONSECUTIVE_FAILURE_WARNING
    ):
        reasons.append(
            "At least one consecutive pipeline "
            "failure is present."
        )

    if (
        success_age_hours is not None
        and success_age_hours
        > HEALTHY_MAX_AGE_HOURS
    ):
        reasons.append(
            "Last successful pipeline run is "
            "older than the normal freshness window."
        )

    if reasons:
        return (
            "WARNING",
            reasons,
        )

    return (
        "HEALTHY",
        [
            "Daily fund pipeline is operating "
            "within the expected freshness window."
        ],
    )


def get_pipeline_health(
    db: Session,
) -> dict[str, Any]:
    """
    Build the complete operational health summary
    for the daily fund pipeline.
    """

    latest_run = (
        get_latest_pipeline_run(
            db=db
        )
    )

    last_success = (
        get_last_successful_pipeline_run(
            db=db
        )
    )

    consecutive_failures = (
        count_consecutive_failures(
            db=db
        )
    )

    success_age_hours = (
        calculate_success_age_hours(
            last_success
        )
    )

    health_status, reasons = (
        determine_pipeline_health(
            latest_run=latest_run,
            last_success=last_success,
            consecutive_failures=
                consecutive_failures,
            success_age_hours=
                success_age_hours,
        )
    )

    return {
        "pipeline_name":
            PIPELINE_NAME,

        "health_status":
            health_status,

        "reasons":
            reasons,

        "latest_run":
            _serialize_run(
                latest_run
            ),

        "last_successful_run":
            _serialize_run(
                last_success
            ),

        "hours_since_last_success":
            success_age_hours,

        "consecutive_failures":
            consecutive_failures,

        "freshness_thresholds":
            {
                "healthy_max_age_hours":
                    HEALTHY_MAX_AGE_HOURS,

                "warning_max_age_hours":
                    WARNING_MAX_AGE_HOURS,
            },

        "checked_at":
            _utc_now_db().isoformat(),
    }


def get_pipeline_run_history(
    db: Session,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Return serialized recent pipeline history.
    """

    runs = get_recent_pipeline_runs(
        db=db,
        limit=limit,
    )

    return {
        "pipeline_name":
            PIPELINE_NAME,

        "count":
            len(runs),

        "runs":
            [
                _serialize_run(
                    run
                )
                for run in runs
            ],
    }
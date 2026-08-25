from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.investments.models.fund_data_sync_run import (
    FundDataSyncRun,
)


def start_sync_run(
    db: Session,
    *,
    pipeline_name: str,
    source_name: str | None = None,
    source_type: str | None = None,
    provider_key: str | None = None,
    source_url: str | None = None,
    source_period: str | None = None,
):
    run = FundDataSyncRun(
        pipeline_name=pipeline_name,
        source_name=source_name,
        source_type=source_type,
        provider_key=provider_key,
        source_url=source_url,
        source_period=source_period,
        status="RUNNING",
        started_at=datetime.utcnow(),
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return run


def complete_sync_run(
    db: Session,
    run: FundDataSyncRun,
    *,
    result: dict | None = None,
    records_received: int | None = None,
    records_processed: int | None = None,
    records_created: int | None = None,
    records_updated: int | None = None,
    records_failed: int | None = None,
    records_unmatched: int | None = None,
    latest_data_date=None,
):
    completed_at = datetime.utcnow()

    run.status = "SUCCESS"
    run.completed_at = completed_at

    run.duration_seconds = int(
        (
            completed_at
            - run.started_at
        ).total_seconds()
    )

    run.records_received = (
        records_received
    )

    run.records_processed = (
        records_processed
    )

    run.records_created = (
        records_created
    )

    run.records_updated = (
        records_updated
    )

    run.records_failed = (
        records_failed
    )

    run.records_unmatched = (
        records_unmatched
    )

    if latest_data_date is not None:
        run.latest_data_date = (
            latest_data_date
        )

    if result is not None:
        run.result_json = json.dumps(
            result,
            default=str,
        )

    db.commit()
    db.refresh(run)

    return run


def fail_sync_run(
    db: Session,
    run: FundDataSyncRun,
    error: Exception,
):
    completed_at = datetime.utcnow()

    run.status = "FAILED"
    run.completed_at = completed_at

    run.duration_seconds = int(
        (
            completed_at
            - run.started_at
        ).total_seconds()
    )

    run.error_type = (
        type(error).__name__
    )

    run.error_message = str(
        error
    )

    db.commit()
    db.refresh(run)

    return run

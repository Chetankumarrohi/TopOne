from __future__ import annotations

import json
import logging
import time

from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.investments.models.fund_pipeline_run import (
    FundPipelineRun,
)

from app.investments.services.amfi_fund_master_service import (
    sync_amfi_fund_master,
)

from app.investments.services.amfi_nav_service import (
    sync_amfi_navs,
)

from app.investments.services.fund_return_service import (
    calculate_all_fund_returns,
    calculate_fund_returns_for_products,
)

from app.investments.services.fund_health_service import (
    calculate_all_fund_health,
    calculate_fund_health_for_products,
)

from app.investments.services.fund_lifecycle_service import (
    classify_all_fund_lifecycles,
)

from app.investments.services.fund_data_validation_service import (
    validate_fund_database,
)

from app.investments.services.fund_pipeline_lock_service import (
    acquire_pipeline_lock,
    release_pipeline_lock,
    generate_lock_owner,
)


logger = logging.getLogger(__name__)


class DailyPipelineError(RuntimeError):
    """Raised when a mandatory daily pipeline step fails."""


def _utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def _utc_now_db() -> datetime:
    """
    Return a naive UTC datetime suitable for the current
    SQLite/SQLAlchemy DateTime columns.
    """
    return datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


def _create_pipeline_run(
    db: Session,
) -> int:

    pipeline_run = FundPipelineRun(
        pipeline_name="DAILY_FUND_PIPELINE",
        status="RUNNING",
        started_at=_utc_now_db(),
    )

    db.add(
        pipeline_run
    )

    db.commit()

    db.refresh(
        pipeline_run
    )

    # IMPORTANT:
    # Downstream services may call db.expunge_all(), which
    # detaches ORM instances from this Session. Persist only
    # the primitive primary-key value across pipeline steps.
    return int(
        pipeline_run.id
    )

def _complete_pipeline_run(
    db: Session,
    pipeline_run_id: int,
    result: dict[str, Any],
) -> None:

    pipeline_run = (
        db.query(
            FundPipelineRun
        )
        .filter(
            FundPipelineRun.id
            == pipeline_run_id
        )
        .first()
    )

    if pipeline_run is None:
        raise DailyPipelineError(
            "Pipeline audit row could not be found "
            f"for run id {pipeline_run_id}."
        )

    pipeline_run.status = (
        result.get("status")
        or "FAILED"
    )

    pipeline_run.finished_at = (
        _utc_now_db()
    )

    pipeline_run.duration_seconds = (
        result.get(
            "duration_seconds"
        )
    )

    pipeline_run.failed_step = (
        result.get(
            "failed_step"
        )
    )

    pipeline_run.result_json = (
        json.dumps(
            result,
            default=str,
        )
    )

    if (
        pipeline_run.status
        == "FAILED"
    ):
        pipeline_run.error_message = (
            "Daily fund pipeline failed"
            + (
                f" at {pipeline_run.failed_step}."
                if pipeline_run.failed_step
                else "."
            )
        )

    elif (
        pipeline_run.status
        == "CRITICAL"
    ):
        pipeline_run.error_message = (
            "Pipeline completed but critical "
            "validation issues were detected."
        )

    else:
        pipeline_run.error_message = None

    db.commit()


def _fail_pipeline_run(
    db: Session,
    pipeline_run_id: int,
    error: Exception,
) -> None:

    pipeline_run = (
        db.query(
            FundPipelineRun
        )
        .filter(
            FundPipelineRun.id
            == pipeline_run_id
        )
        .first()
    )

    if pipeline_run is None:
        logger.error(
            "Unable to mark pipeline run %s as FAILED "
            "because its audit row was not found.",
            pipeline_run_id,
        )
        return

    finished_at = (
        _utc_now_db()
    )

    pipeline_run.status = (
        "FAILED"
    )

    pipeline_run.finished_at = (
        finished_at
    )

    if pipeline_run.started_at:
        pipeline_run.duration_seconds = (
            finished_at
            - pipeline_run.started_at
        ).total_seconds()

    pipeline_run.error_message = (
        f"{type(error).__name__}: "
        f"{error}"
    )

    db.commit()


def _run_step(
    *,
    name: str,
    function: Callable[..., Any],
    db: Session,
    kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:

    kwargs = kwargs or {}

    started_at = _utc_now_iso()
    start_time = time.perf_counter()

    logger.info(
        "Starting daily pipeline step: %s",
        name,
    )

    try:
        result = function(
            db=db,
            **kwargs,
        )

        duration_seconds = round(
            time.perf_counter()
            - start_time,
            2,
        )

        logger.info(
            "Completed daily pipeline step: %s "
            "(%.2f seconds)",
            name,
            duration_seconds,
        )

        return {
            "name": name,
            "status": "SUCCESS",
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "duration_seconds":
                duration_seconds,
            "result": result,
            "error": None,
        }

    except Exception as exc:
        db.rollback()

        duration_seconds = round(
            time.perf_counter()
            - start_time,
            2,
        )

        logger.exception(
            "Daily pipeline step failed: %s",
            name,
        )

        return {
            "name": name,
            "status": "FAILED",
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "duration_seconds":
                duration_seconds,
            "result": None,
            "error": (
                f"{type(exc).__name__}: {exc}"
            ),
        }


def run_daily_fund_pipeline(
    db: Session,
) -> dict[str, Any]:
    """
    Run the mandatory daily mutual-fund data pipeline.

    Order matters:

    1. Synchronize AMFI master data.
    2. Synchronize current NAV data.
    3. Recalculate returns.
    4. Recalculate fund health.
    5. Reclassify lifecycle state.
    6. Validate the resulting database.

    The pipeline stops if a mandatory processing
    step fails. Validation is performed last.
    """

    pipeline_started_at = _utc_now_iso()
    pipeline_start_time = time.perf_counter()

    lock_owner = generate_lock_owner()

    lock_acquired = acquire_pipeline_lock(
        db,
        owner=lock_owner,
    )

    if not lock_acquired:
        logger.warning(
            "Daily fund pipeline skipped because another "
            "execution currently owns the database lock."
        )

        return {
            "pipeline_run_id": None,
            "status": "SKIPPED_LOCKED",
            "started_at": pipeline_started_at,
            "finished_at": _utc_now_iso(),
            "duration_seconds": round(
                time.perf_counter() - pipeline_start_time,
                2,
            ),
            "failed_step": None,
            "steps": [],
            "reason": (
                "Another daily fund pipeline execution "
                "currently owns the database lock."
            ),
        }

    pipeline_run_id: int | None = None

    try:
        pipeline_run_id = _create_pipeline_run(
            db=db,
        )

        steps: list[dict[str, Any]] = []

        # ----------------------------------------------------
        # 1. AMFI master synchronization
        # ----------------------------------------------------
        master_step = _run_step(
            name="AMFI_MASTER_SYNC",
            function=sync_amfi_fund_master,
            db=db,
        )
        steps.append(master_step)

        if master_step["status"] == "FAILED":
            result = {
                "pipeline_run_id": pipeline_run_id,
                "status": "FAILED",
                "started_at": pipeline_started_at,
                "finished_at": _utc_now_iso(),
                "duration_seconds": round(
                    time.perf_counter()
                    - pipeline_start_time,
                    2,
                ),
                "failed_step": "AMFI_MASTER_SYNC",
                "steps": steps,
            }
            _complete_pipeline_run(
                db=db,
                pipeline_run_id=pipeline_run_id,
                result=result,
            )
            return result

        # ----------------------------------------------------
        # 2. Latest NAV synchronization
        # ----------------------------------------------------
        nav_step = _run_step(
            name="AMFI_NAV_SYNC",
            function=sync_amfi_navs,
            db=db,
        )
        steps.append(nav_step)

        if nav_step["status"] == "FAILED":
            result = {
                "pipeline_run_id": pipeline_run_id,
                "status": "FAILED",
                "started_at": pipeline_started_at,
                "finished_at": _utc_now_iso(),
                "duration_seconds": round(
                    time.perf_counter()
                    - pipeline_start_time,
                    2,
                ),
                "failed_step": "AMFI_NAV_SYNC",
                "steps": steps,
            }
            _complete_pipeline_run(
                db=db,
                pipeline_run_id=pipeline_run_id,
                result=result,
            )
            return result

        # Combine IDs from both synchronization stages. A set
        # prevents duplicate recalculation when both stages
        # report the same product.
        master_result = master_step["result"] or {}
        nav_result = nav_step["result"] or {}

        changed_product_ids = sorted(
            {
                int(product_id)
                for product_id in (
                    list(
                        master_result.get(
                            "changed_product_ids",
                            [],
                        )
                        or []
                    )
                    + list(
                        nav_result.get(
                            "changed_product_ids",
                            [],
                        )
                        or []
                    )
                )
                if product_id is not None
            }
        )

        logger.info(
            "Daily pipeline detected %s changed fund products.",
            len(changed_product_ids),
        )

        # ----------------------------------------------------
        # 3. Incremental return calculation
        # ----------------------------------------------------
        returns_step = _run_step(
            name="FUND_RETURNS",
            function=calculate_fund_returns_for_products,
            db=db,
            kwargs={
                "product_ids": changed_product_ids,
                "batch_size": 100,
            },
        )
        steps.append(returns_step)

        if returns_step["status"] == "FAILED":
            result = {
                "pipeline_run_id": pipeline_run_id,
                "status": "FAILED",
                "started_at": pipeline_started_at,
                "finished_at": _utc_now_iso(),
                "duration_seconds": round(
                    time.perf_counter()
                    - pipeline_start_time,
                    2,
                ),
                "failed_step": "FUND_RETURNS",
                "steps": steps,
            }
            _complete_pipeline_run(
                db=db,
                pipeline_run_id=pipeline_run_id,
                result=result,
            )
            return result

        # ----------------------------------------------------
        # 4. Incremental base Fund Health calculation
        # ----------------------------------------------------
        health_step = _run_step(
            name="FUND_HEALTH",
            function=calculate_fund_health_for_products,
            db=db,
            kwargs={
                "product_ids": changed_product_ids,
                "batch_size": 100,
            },
        )
        steps.append(health_step)

        if health_step["status"] == "FAILED":
            result = {
                "pipeline_run_id": pipeline_run_id,
                "status": "FAILED",
                "started_at": pipeline_started_at,
                "finished_at": _utc_now_iso(),
                "duration_seconds": round(
                    time.perf_counter()
                    - pipeline_start_time,
                    2,
                ),
                "failed_step": "FUND_HEALTH",
                "steps": steps,
            }
            _complete_pipeline_run(
                db=db,
                pipeline_run_id=pipeline_run_id,
                result=result,
            )
            return result

        # ----------------------------------------------------
        # 5. Lifecycle classification
        # ----------------------------------------------------
        lifecycle_step = _run_step(
            name="FUND_LIFECYCLE",
            function=classify_all_fund_lifecycles,
            db=db,
            kwargs={
                "batch_size": 500,
            },
        )
        steps.append(lifecycle_step)

        if lifecycle_step["status"] == "FAILED":
            result = {
                "pipeline_run_id": pipeline_run_id,
                "status": "FAILED",
                "started_at": pipeline_started_at,
                "finished_at": _utc_now_iso(),
                "duration_seconds": round(
                    time.perf_counter()
                    - pipeline_start_time,
                    2,
                ),
                "failed_step": "FUND_LIFECYCLE",
                "steps": steps,
            }
            _complete_pipeline_run(
                db=db,
                pipeline_run_id=pipeline_run_id,
                result=result,
            )
            return result

        validation_step = _run_step(
            name="DATA_VALIDATION",
            function=validate_fund_database,
            db=db,
        )

        steps.append(
            validation_step
        )

        if (
            validation_step["status"]
            == "FAILED"
        ):
            final_status = "FAILED"

        else:
            validation_result = (
                validation_step["result"]
                or {}
            )

            critical_issues = (
                validation_result.get(
                    "critical_issues",
                    0,
                )
            )

            if critical_issues > 0:
                final_status = (
                    "CRITICAL"
                )
            else:
                final_status = (
                    "SUCCESS"
                )

        result = {
            "pipeline_run_id":
                pipeline_run_id,

            "status":
                final_status,

            "started_at":
                pipeline_started_at,

            "finished_at":
                _utc_now_iso(),

            "duration_seconds": round(
                time.perf_counter()
                - pipeline_start_time,
                2,
            ),

            "failed_step":
                (
                    "DATA_VALIDATION"
                    if final_status
                    == "FAILED"
                    else None
                ),

            "changed_products":
                len(changed_product_ids),

            "changed_product_ids":
                changed_product_ids,

            "steps":
                steps,
        }

        _complete_pipeline_run(
            db=db,
            pipeline_run_id=
                pipeline_run_id,
            result=result,
        )

        return result

    except Exception as exc:
        db.rollback()

        logger.exception(
            "Unexpected daily fund "
            "pipeline failure."
        )

        if pipeline_run_id is not None:
            try:
                _fail_pipeline_run(
                    db=db,
                    pipeline_run_id=
                        pipeline_run_id,
                    error=exc,
                )

            except Exception:
                db.rollback()

                logger.exception(
                    "Unable to persist FAILED "
                    "pipeline audit state."
                )

        raise

    finally:
        try:
            released = release_pipeline_lock(
                db,
                owner=lock_owner,
            )

            if not released:
                logger.warning(
                    "Daily fund pipeline lock was not "
                    "released because this execution "
                    "was no longer the lock owner."
                )

        except Exception:
            db.rollback()

            logger.exception(
                "Unable to release daily fund "
                "pipeline database lock."
            )

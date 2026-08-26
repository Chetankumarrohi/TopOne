from __future__ import annotations

import logging
import threading

from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
)

from apscheduler.schedulers.background import (
    BackgroundScheduler,
)

from apscheduler.triggers.cron import (
    CronTrigger,
)

from app.core.database import (
    SessionLocal,
)

from app.investments.services.daily_fund_pipeline import (
    run_daily_fund_pipeline,
)


logger = logging.getLogger(__name__)


# =========================================================
# SCHEDULER CONFIGURATION
# =========================================================

SCHEDULER_TIMEZONE = "Asia/Kolkata"

DAILY_PIPELINE_JOB_ID = "daily_fund_pipeline"
DAILY_SNAPSHOT_JOB_ID = "daily_portfolio_snapshots"


# =========================================================
# PROCESS-LOCAL STATE
# =========================================================

_scheduler: BackgroundScheduler | None = None

_scheduler_lock = threading.Lock()


# =========================================================
# INCIDENT + ALERT SYNCHRONIZATION
# =========================================================

def _sync_incidents_and_alerts_after_pipeline(
    db,
):
    """
    Synchronize operational incidents after every
    scheduled pipeline execution and then deliver any
    pending alerts.

    Imports are intentionally local to avoid circular
    dependencies between:

        scheduler
        -> incident persistence
        -> incident detection
        -> pipeline status
        -> scheduler

    Incident or alert failures are logged but do not
    replace or hide the original pipeline result.
    """

    try:
        # -------------------------------------------------
        # INCIDENT PERSISTENCE
        # -------------------------------------------------

        from app.investments.services.fund_pipeline_incident_persistence_service import (
            sync_pipeline_incidents,
        )

        incident_result = (
            sync_pipeline_incidents(
                db=db,
            )
        )

        logger.info(
            "Pipeline incident synchronization "
            "completed. level=%s "
            "created=%s updated=%s resolved=%s",
            incident_result.get(
                "incident_level"
            ),
            incident_result.get(
                "created"
            ),
            incident_result.get(
                "updated"
            ),
            incident_result.get(
                "resolved"
            ),
        )

    except Exception:
        logger.exception(
            "Pipeline incident synchronization failed."
        )

        # If incident synchronization itself fails,
        # do not attempt alert delivery because the
        # incident state may not be reliable.
        return {
            "incident_sync":
                None,

            "alert_delivery":
                None,
        }

    try:
        # -------------------------------------------------
        # EMAIL ALERT DELIVERY
        # -------------------------------------------------

        from app.investments.services.fund_pipeline_alert_service import (
            send_pending_pipeline_alerts,
        )

        alert_result = (
            send_pending_pipeline_alerts(
                db=db,
            )
        )

        logger.info(
            "Pipeline alert delivery completed. "
            "enabled=%s pending=%s "
            "sent=%s failed=%s",
            alert_result.get(
                "enabled"
            ),
            alert_result.get(
                "pending"
            ),
            alert_result.get(
                "sent"
            ),
            alert_result.get(
                "failed"
            ),
        )

    except Exception:
        logger.exception(
            "Pipeline alert delivery failed."
        )

        alert_result = None

    return {
        "incident_sync":
            incident_result,

        "alert_delivery":
            alert_result,
    }


# =========================================================
# JOB EXECUTION
# =========================================================

def execute_daily_fund_pipeline():
    """
    Scheduler entry point for the daily fund pipeline.

    A fresh SQLAlchemy session is created for every
    scheduled execution and always closed afterwards.

    After the pipeline attempt:

        1. Operational incidents are synchronized.
        2. Pending incident alerts are delivered.

    This runs whether the main pipeline succeeds or
    raises an exception.
    """

    logger.info(
        "Scheduled daily fund pipeline "
        "execution started."
    )

    db = SessionLocal()

    try:
        result = (
            run_daily_fund_pipeline(
                db=db,
            )
        )

        logger.info(
            "Scheduled daily fund pipeline "
            "completed with status=%s "
            "run_id=%s duration=%s",
            result.get(
                "status"
            ),
            result.get(
                "pipeline_run_id"
            ),
            result.get(
                "duration_seconds"
            ),
        )

        return result

    except Exception:
        logger.exception(
            "Scheduled daily fund pipeline "
            "execution failed."
        )

        raise

    finally:
        # -------------------------------------------------
        # INCIDENT + ALERT PROCESSING
        # -------------------------------------------------

        _sync_incidents_and_alerts_after_pipeline(
            db=db,
        )

        db.close()


def execute_daily_portfolio_snapshots():
    """
    Scheduler entry point for daily portfolio snapshot capturing.

    Runs after the daily fund pipeline (at 03:00 IST) to snapshot
    all active users with holdings using fresh NAV valuation data.
    """
    logger.info("Scheduled daily portfolio snapshot execution started.")

    from app.investments.services.portfolio_snapshot_batch_service import (
        run_daily_portfolio_snapshots,
    )

    db = SessionLocal()

    try:
        result = run_daily_portfolio_snapshots(db=db)

        logger.info(
            "Scheduled daily portfolio snapshots completed: total=%d succeeded=%d failed=%d duration=%ss",
            result.get("total_users", 0),
            result.get("succeeded", 0),
            result.get("failed", 0),
            result.get("duration_seconds", 0.0),
        )

        return result

    except Exception:
        logger.exception("Scheduled daily portfolio snapshots execution failed.")
        raise

    finally:
        db.close()


# =========================================================
# EVENT LISTENER
# =========================================================

def _scheduler_event_listener(
    event,
):
    """
    Log important APScheduler execution events.
    """

    if event.code == EVENT_JOB_EXECUTED:
        logger.info(
            "Scheduler job completed: %s",
            event.job_id,
        )

    elif event.code == EVENT_JOB_MISSED:
        logger.warning(
            "Scheduler job missed: %s",
            event.job_id,
        )

    elif event.code == EVENT_JOB_ERROR:
        logger.error(
            "Scheduler job failed: %s",
            event.job_id,
        )


# =========================================================
# SCHEDULER FACTORY
# =========================================================

def _build_scheduler(
) -> BackgroundScheduler:
    """
    Build and configure the process-local APScheduler.
    """

    scheduler = BackgroundScheduler(
        timezone=SCHEDULER_TIMEZONE,
    )

    scheduler.add_listener(
        _scheduler_event_listener,
        EVENT_JOB_EXECUTED
        | EVENT_JOB_ERROR
        | EVENT_JOB_MISSED,
    )

    # -----------------------------------------------------
    # DAILY FUND PIPELINE
    # -----------------------------------------------------
    #
    # Runs every day at 02:00 IST.
    # -----------------------------------------------------

    scheduler.add_job(
        execute_daily_fund_pipeline,

        trigger=CronTrigger(
            hour=2,
            minute=0,
            timezone=SCHEDULER_TIMEZONE,
        ),

        id=DAILY_PIPELINE_JOB_ID,

        replace_existing=True,

        # Never allow two instances of this scheduler
        # job to execute simultaneously in this process.
        max_instances=1,

        # If multiple executions were missed while the
        # application was unavailable, execute only the
        # latest eligible run.
        coalesce=True,

        # Allow a missed execution to run if the server
        # comes back within 60 minutes.
        misfire_grace_time=3600,
    )

    # -----------------------------------------------------
    # DAILY PORTFOLIO SNAPSHOTS
    # -----------------------------------------------------
    #
    # Runs every day at 03:00 IST (after fund pipeline).
    # -----------------------------------------------------

    scheduler.add_job(
        execute_daily_portfolio_snapshots,

        trigger=CronTrigger(
            hour=3,
            minute=0,
            timezone=SCHEDULER_TIMEZONE,
        ),

        id=DAILY_SNAPSHOT_JOB_ID,

        replace_existing=True,

        max_instances=1,

        coalesce=True,

        misfire_grace_time=3600,
    )

    return scheduler



# =========================================================
# START SCHEDULER
# =========================================================

def start_fund_scheduler(
) -> BackgroundScheduler:
    """
    Start the process-local fund scheduler.

    Repeated calls inside the same Python process return
    the existing running scheduler instead of creating
    another instance.
    """

    global _scheduler

    with _scheduler_lock:

        if (
            _scheduler is not None
            and _scheduler.running
        ):
            logger.info(
                "Fund scheduler is already "
                "running."
            )

            return _scheduler

        scheduler = (
            _build_scheduler()
        )

        scheduler.start()

        _scheduler = scheduler

        job = scheduler.get_job(
            DAILY_PIPELINE_JOB_ID
        )

        logger.info(
            "Fund scheduler started. "
            "Next daily pipeline run: %s",
            (
                job.next_run_time
                if job
                else None
            ),
        )

        return scheduler


# =========================================================
# STOP SCHEDULER
# =========================================================

def stop_fund_scheduler():
    """
    Shut down the process-local scheduler.
    """

    global _scheduler

    with _scheduler_lock:

        if _scheduler is None:
            logger.info(
                "Fund scheduler is already stopped."
            )

            return

        if _scheduler.running:
            _scheduler.shutdown(
                wait=False,
            )

        _scheduler = None

        logger.info(
            "Fund scheduler stopped."
        )


# =========================================================
# SCHEDULER STATUS
# =========================================================

def get_fund_scheduler_status() -> dict:
    """
    Return the current process-local scheduler state.
    """

    scheduler = _scheduler

    if scheduler is None or not scheduler.running:
        return {
            "running": False,
            "timezone": SCHEDULER_TIMEZONE,
            "job_id": DAILY_PIPELINE_JOB_ID,
            "next_run_time": None,
            "jobs": {},
        }

    pipeline_job = scheduler.get_job(DAILY_PIPELINE_JOB_ID)
    snapshot_job = scheduler.get_job(DAILY_SNAPSHOT_JOB_ID)

    return {
        "running": True,
        "timezone": SCHEDULER_TIMEZONE,
        "job_id": DAILY_PIPELINE_JOB_ID,
        "next_run_time": (
            pipeline_job.next_run_time.isoformat()
            if (pipeline_job and pipeline_job.next_run_time)
            else None
        ),
        "jobs": {
            DAILY_PIPELINE_JOB_ID: (
                pipeline_job.next_run_time.isoformat()
                if (pipeline_job and pipeline_job.next_run_time)
                else None
            ),
            DAILY_SNAPSHOT_JOB_ID: (
                snapshot_job.next_run_time.isoformat()
                if (snapshot_job and snapshot_job.next_run_time)
                else None
            ),
        },
    }
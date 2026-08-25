from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.auth.dependencies import (
    require_admin_user,
)

from app.investments.services.fund_pipeline_health_service import (
    get_pipeline_health,
    get_pipeline_run_history,
)

from app.investments.services.fund_pipeline_status_service import (
    get_pipeline_status,
)

from app.investments.services.fund_pipeline_incident_service import (
    detect_pipeline_incident,
)

from app.investments.services.fund_pipeline_incident_persistence_service import (
    acknowledge_pipeline_incident,
    get_open_pipeline_incidents,
    get_pipeline_incident_history,
    mark_pipeline_incident_alert_sent,
    sync_pipeline_incidents,
)


router = APIRouter(
    prefix="/admin/pipeline",
    tags=["Pipeline Admin"],
    dependencies=[
        Depends(require_admin_user),
    ],
)


# ============================================================
# PIPELINE HEALTH
# ============================================================

@router.get("/health")
def pipeline_health(
    db: Session = Depends(get_db),
):
    return get_pipeline_health(
        db=db
    )


@router.get("/runs")
def pipeline_runs(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    return get_pipeline_run_history(
        db=db,
        limit=limit,
    )


@router.get("/status")
def pipeline_status(
    db: Session = Depends(get_db),
):
    return get_pipeline_status(
        db=db
    )


# ============================================================
# INCIDENT DETECTION
# ============================================================

@router.get("/incidents")
def pipeline_incidents(
    db: Session = Depends(get_db),
):
    return detect_pipeline_incident(
        db=db
    )


# ============================================================
# INCIDENT PERSISTENCE
# ============================================================

@router.post("/incidents/sync")
def sync_incidents(
    db: Session = Depends(get_db),
):
    return sync_pipeline_incidents(
        db=db
    )


@router.get("/incidents/open")
def open_incidents(
    db: Session = Depends(get_db),
):
    return {
        "incidents":
            get_open_pipeline_incidents(
                db=db
            )
    }


@router.get("/incidents/history")
def incident_history(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
):
    return {
        "incidents":
            get_pipeline_incident_history(
                db=db,
                limit=limit,
            )
    }


# ============================================================
# INCIDENT ACTIONS
# ============================================================

@router.post(
    "/incidents/{incident_id}/acknowledge"
)
def acknowledge_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_admin_user
    ),
):
    try:
        return acknowledge_pipeline_incident(
            db=db,
            incident_id=incident_id,
            user_id=current_user.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/incidents/{incident_id}/mark-alert-sent"
)
def mark_incident_alert_sent(
    incident_id: int,
    db: Session = Depends(get_db),
):
    try:
        return mark_pipeline_incident_alert_sent(
            db=db,
            incident_id=incident_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
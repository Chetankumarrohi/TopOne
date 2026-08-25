from __future__ import annotations

import json

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.investments.models.fund_pipeline_incident import (
    FundPipelineIncident,
)

from app.investments.services.fund_pipeline_incident_service import (
    detect_pipeline_incident,
)


def _utc_now_db() -> datetime:
    return datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


def _get_open_incident(
    db: Session,
    incident_code: str,
) -> FundPipelineIncident | None:
    """
    Return the currently open incident for a code,
    if one exists.
    """

    return (
        db.query(
            FundPipelineIncident
        )
        .filter(
            FundPipelineIncident.incident_code
            == incident_code,

            FundPipelineIncident.status
            == "OPEN",
        )
        .order_by(
            FundPipelineIncident.id.desc()
        )
        .first()
    )


def _serialize_incident(
    incident: FundPipelineIncident,
) -> dict[str, Any]:
    return {
        "id":
            incident.id,

        "incident_code":
            incident.incident_code,

        "severity":
            incident.severity,

        "status":
            incident.status,

        "message":
            incident.message,

        "first_detected_at":
            (
                incident.first_detected_at.isoformat()
                if incident.first_detected_at
                else None
            ),

        "last_detected_at":
            (
                incident.last_detected_at.isoformat()
                if incident.last_detected_at
                else None
            ),

        "resolved_at":
            (
                incident.resolved_at.isoformat()
                if incident.resolved_at
                else None
            ),

        "acknowledged":
            incident.acknowledged,

        "acknowledged_at":
            (
                incident.acknowledged_at.isoformat()
                if incident.acknowledged_at
                else None
            ),

        "acknowledged_by_user_id":
            incident.acknowledged_by_user_id,

        "alert_sent":
            incident.alert_sent,

        "alert_sent_at":
            (
                incident.alert_sent_at.isoformat()
                if incident.alert_sent_at
                else None
            ),
    }


def sync_pipeline_incidents(
    db: Session,
) -> dict[str, Any]:
    """
    Persist the currently detected pipeline incidents.

    Behavior:

    1. New incident code:
       create OPEN incident.

    2. Existing OPEN incident:
       update severity/message/last_detected_at.

    3. Previously OPEN incident no longer detected:
       mark RESOLVED.

    This prevents duplicate rows for the same continuing
    operational problem.
    """

    detection = (
        detect_pipeline_incident(
            db=db
        )
    )

    now = _utc_now_db()

    detected_incidents = (
        detection.get(
            "incidents",
            [],
        )
        or []
    )

    detected_codes = {
        str(
            incident.get(
                "code"
            )
        )
        for incident in detected_incidents
        if incident.get(
            "code"
        )
    }

    created = 0
    updated = 0
    resolved = 0

    active_records = []

    # ========================================================
    # CREATE OR UPDATE CURRENT INCIDENTS
    # ========================================================

    for detected in detected_incidents:

        incident_code = (
            detected.get(
                "code"
            )
        )

        if not incident_code:
            continue

        severity = (
            detected.get(
                "severity",
                "WARNING",
            )
        )

        message = (
            detected.get(
                "message",
                incident_code,
            )
        )

        existing = (
            _get_open_incident(
                db=db,
                incident_code=
                    incident_code,
            )
        )

        details_json = (
            json.dumps(
                detected,
                default=str,
            )
        )

        if existing is None:

            existing = (
                FundPipelineIncident(
                    incident_code=
                        incident_code,

                    severity=
                        severity,

                    status=
                        "OPEN",

                    message=
                        message,

                    first_detected_at=
                        now,

                    last_detected_at=
                        now,

                    details_json=
                        details_json,

                    acknowledged=
                        False,

                    alert_sent=
                        False,
                )
            )

            db.add(
                existing
            )

            db.flush()

            created += 1

        else:

            existing.severity = (
                severity
            )

            existing.message = (
                message
            )

            existing.last_detected_at = (
                now
            )

            existing.details_json = (
                details_json
            )

            updated += 1

        active_records.append(
            existing
        )

    # ========================================================
    # RESOLVE INCIDENTS THAT DISAPPEARED
    # ========================================================

    open_incidents = (
        db.query(
            FundPipelineIncident
        )
        .filter(
            FundPipelineIncident.status
            == "OPEN"
        )
        .all()
    )

    for incident in open_incidents:

        if (
            incident.incident_code
            not in detected_codes
        ):
            incident.status = (
                "RESOLVED"
            )

            incident.resolved_at = (
                now
            )

            incident.last_detected_at = (
                now
            )

            resolved += 1

    db.commit()

    return {
        "incident_active":
            detection.get(
                "incident_active",
                False,
            ),

        "incident_level":
            detection.get(
                "incident_level",
                "NONE",
            ),

        "created":
            created,

        "updated":
            updated,

        "resolved":
            resolved,

        "active_incidents":
            [
                _serialize_incident(
                    incident
                )
                for incident
                in active_records
            ],

        "synced_at":
            now.isoformat(),
    }


def get_open_pipeline_incidents(
    db: Session,
) -> list[dict[str, Any]]:
    """
    Return all currently open incidents.
    """

    incidents = (
        db.query(
            FundPipelineIncident
        )
        .filter(
            FundPipelineIncident.status
            == "OPEN"
        )
        .order_by(
            FundPipelineIncident.severity.desc(),
            FundPipelineIncident.id.desc(),
        )
        .all()
    )

    return [
        _serialize_incident(
            incident
        )
        for incident in incidents
    ]


def get_pipeline_incident_history(
    db: Session,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Return recent incident history.
    """

    limit = max(
        1,
        min(
            int(limit),
            200,
        ),
    )

    incidents = (
        db.query(
            FundPipelineIncident
        )
        .order_by(
            FundPipelineIncident.id.desc()
        )
        .limit(
            limit
        )
        .all()
    )

    return [
        _serialize_incident(
            incident
        )
        for incident in incidents
    ]
def acknowledge_pipeline_incident(
    db: Session,
    incident_id: int,
    user_id: int,
) -> dict[str, Any]:
    """
    Mark an OPEN incident as acknowledged by an admin.
    """

    incident = (
        db.query(
            FundPipelineIncident
        )
        .filter(
            FundPipelineIncident.id
            == incident_id
        )
        .first()
    )

    if incident is None:
        raise ValueError(
            "Pipeline incident not found."
        )

    if incident.status != "OPEN":
        raise ValueError(
            "Only OPEN incidents can be acknowledged."
        )

    if incident.acknowledged:
        return _serialize_incident(
            incident
        )

    now = _utc_now_db()

    incident.acknowledged = True
    incident.acknowledged_at = now
    incident.acknowledged_by_user_id = (
        user_id
    )

    db.commit()
    db.refresh(
        incident
    )

    return _serialize_incident(
        incident
    )


def mark_pipeline_incident_alert_sent(
    db: Session,
    incident_id: int,
) -> dict[str, Any]:
    """
    Mark an incident as already alerted.

    This is used to suppress duplicate notifications
    while the same incident remains OPEN.
    """

    incident = (
        db.query(
            FundPipelineIncident
        )
        .filter(
            FundPipelineIncident.id
            == incident_id
        )
        .first()
    )

    if incident is None:
        raise ValueError(
            "Pipeline incident not found."
        )

    if incident.alert_sent:
        return _serialize_incident(
            incident
        )

    now = _utc_now_db()

    incident.alert_sent = True
    incident.alert_sent_at = now

    db.commit()
    db.refresh(
        incident
    )

    return _serialize_incident(
        incident
    )
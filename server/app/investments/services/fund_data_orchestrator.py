from __future__ import annotations

from datetime import date, datetime, timezone
from time import perf_counter
from typing import Any, Callable

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.investments.models.investment_product import InvestmentProduct
from app.investments.services.amfi_fund_master_service import sync_amfi_fund_master
from app.investments.services.amfi_nav_service import sync_amfi_navs
from app.investments.services.fund_return_service import calculate_all_fund_returns
from app.investments.services.fund_health_service import calculate_all_fund_health
from app.investments.services.amc_factsheet_metadata_service import (
    sync_bajaj_factsheet_metadata,
)

from app.investments.services.fund_data_sync_audit_service import (
    start_sync_run,
    complete_sync_run,
    fail_sync_run,
)

MONTHLY_METADATA_PROVIDERS: dict[str, Callable[[Session], dict[str, Any]]] = {
    "BAJAJ_FINSERV": sync_bajaj_factsheet_metadata,
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_stage(
    db: Session,
    name: str,
    fn: Callable[[], Any],
    *,
    source_name: str | None = None,
    source_type: str | None = None,
    provider_key: str | None = None,
    source_url: str | None = None,
    source_period: str | None = None,
) -> dict[str, Any]:
    """
    Run one pipeline stage and persist an audit row.

    The audit record is created before execution and finalized as
    SUCCESS or FAILED after the stage completes.
    """
    started_at = _utc_now_iso()
    started_clock = perf_counter()

    audit_run = start_sync_run(
        db=db,
        pipeline_name=name,
        source_name=source_name,
        source_type=source_type,
        provider_key=provider_key,
        source_url=source_url,
        source_period=source_period,
    )

    try:
        result = fn()

        duration_seconds = round(
            perf_counter() - started_clock,
            3,
        )

        records_received = None
        records_processed = None
        records_created = None
        records_updated = None
        records_failed = None
        records_unmatched = None

        if isinstance(result, dict):
            records_received = (
                result.get("records_received")
            )

            records_processed = (
                result.get("processed")
                or result.get("records_processed")
            )

            records_created = (
                result.get("products_created")
                or result.get("records_created")
            )

            records_updated = (
                result.get("updated")
                or result.get("products_updated")
                or result.get("records_updated")
            )

            records_failed = (
                result.get("failed")
                or result.get("records_failed")
            )

            records_unmatched = (
                result.get("unmatched")
                or result.get("records_unmatched")
            )

        complete_sync_run(
            db=db,
            run=audit_run,
            result=(
                result
                if isinstance(result, dict)
                else {
                    "result": result
                }
            ),
            records_received=records_received,
            records_processed=records_processed,
            records_created=records_created,
            records_updated=records_updated,
            records_failed=records_failed,
            records_unmatched=records_unmatched,
        )

        return {
            "stage":
                name,

            "audit_run_id":
                audit_run.id,

            "status":
                "SUCCESS",

            "started_at":
                started_at,

            "completed_at":
                _utc_now_iso(),

            "duration_seconds":
                duration_seconds,

            "result":
                result,
        }

    except Exception as error:
        duration_seconds = round(
            perf_counter() - started_clock,
            3,
        )

        fail_sync_run(
            db=db,
            run=audit_run,
            error=error,
        )

        return {
            "stage":
                name,

            "audit_run_id":
                audit_run.id,

            "status":
                "FAILED",

            "started_at":
                started_at,

            "completed_at":
                _utc_now_iso(),

            "duration_seconds":
                duration_seconds,

            "error_type":
                type(error).__name__,

            "error":
                str(error),
        }


def _pipeline_succeeded(stages: list[dict[str, Any]]) -> bool:
    return all(stage.get("status") == "SUCCESS" for stage in stages)


def run_daily_fund_pipeline(
    db: Session,
    *,
    return_batch_size: int = 100,
    health_batch_size: int = 100,
    run_nav_only_sync: bool = False,
) -> dict[str, Any]:
    """
    Daily pipeline:
    AMFI master/latest NAV -> returns -> Fund Form -> health snapshot.

    sync_amfi_fund_master() already updates current NAV and NAV history,
    so the separate sync_amfi_navs() call is disabled by default.
    """
    pipeline_started_at = _utc_now_iso()
    stages: list[dict[str, Any]] = []

    master_stage = _run_stage(
        db,
        "amfi_master_and_nav",
        lambda: sync_amfi_fund_master(db=db),
        source_name="AMFI NAVAll",
        source_type="AMFI",
    )
    stages.append(master_stage)

    if master_stage["status"] != "SUCCESS":
        return {
            "pipeline": "DAILY_FUND_PIPELINE",
            "status": "FAILED",
            "started_at": pipeline_started_at,
            "completed_at": _utc_now_iso(),
            "stages": stages,
            "message": "AMFI ingestion failed. Dependent stages were not run.",
        }

    if run_nav_only_sync:
        nav_stage = _run_stage(
            db,
            "amfi_nav_only_sync",
            lambda: sync_amfi_navs(db=db),
            source_name="AMFI Latest NAV",
            source_type="AMFI",
        )
        stages.append(nav_stage)

        if nav_stage["status"] != "SUCCESS":
            return {
                "pipeline": "DAILY_FUND_PIPELINE",
                "status": "FAILED",
                "started_at": pipeline_started_at,
                "completed_at": _utc_now_iso(),
                "stages": stages,
                "message": "NAV-only sync failed. Dependent stages were not run.",
            }

    returns_stage = _run_stage(
        db,
        "fund_returns",
        lambda: calculate_all_fund_returns(
            db=db,
            batch_size=return_batch_size,
        ),
        source_name="TopOne Analytics",
        source_type="INTERNAL",
    )
    stages.append(returns_stage)

    if returns_stage["status"] != "SUCCESS":
        return {
            "pipeline": "DAILY_FUND_PIPELINE",
            "status": "FAILED",
            "started_at": pipeline_started_at,
            "completed_at": _utc_now_iso(),
            "stages": stages,
            "message": "Return calculation failed. Fund Form was not recalculated.",
        }

    health_stage = _run_stage(
        db,
        "fund_form",
        lambda: calculate_all_fund_health(
            db=db,
            batch_size=health_batch_size,
        ),
        source_name="TopOne Fund Form",
        source_type="INTERNAL",
    )
    stages.append(health_stage)

    if health_stage["status"] != "SUCCESS":
        return {
            "pipeline": "DAILY_FUND_PIPELINE",
            "status": "FAILED",
            "started_at": pipeline_started_at,
            "completed_at": _utc_now_iso(),
            "stages": stages,
            "message": "Fund Form calculation failed.",
        }

    return {
        "pipeline": "DAILY_FUND_PIPELINE",
        "status": "SUCCESS" if _pipeline_succeeded(stages) else "FAILED",
        "started_at": pipeline_started_at,
        "completed_at": _utc_now_iso(),
        "stages": stages,
        "data_health": get_fund_data_health(db=db),
    }


def run_nav_only_pipeline(db: Session) -> dict[str, Any]:
    stage = _run_stage(
        db,
        "amfi_nav_only_sync",
        lambda: sync_amfi_navs(db=db),
        source_name="AMFI Latest NAV",
        source_type="AMFI",
    )

    return {
        "pipeline": "NAV_ONLY_PIPELINE",
        "status": stage["status"],
        "started_at": stage["started_at"],
        "completed_at": stage["completed_at"],
        "stages": [stage],
    }


def run_monthly_fund_pipeline(
    db: Session,
    *,
    providers: list[str] | None = None,
) -> dict[str, Any]:
    """
    Runs all validated AMC metadata adapters.
    Add new AMC adapters to MONTHLY_METADATA_PROVIDERS as we implement them.
    """
    pipeline_started_at = _utc_now_iso()

    requested_providers = (
        providers
        if providers is not None
        else list(MONTHLY_METADATA_PROVIDERS.keys())
    )

    unknown_providers = [
        provider
        for provider in requested_providers
        if provider not in MONTHLY_METADATA_PROVIDERS
    ]

    if unknown_providers:
        return {
            "pipeline": "MONTHLY_FUND_PIPELINE",
            "status": "FAILED",
            "started_at": pipeline_started_at,
            "completed_at": _utc_now_iso(),
            "unknown_providers": unknown_providers,
            "registered_providers": list(MONTHLY_METADATA_PROVIDERS.keys()),
            "stages": [],
        }

    stages: list[dict[str, Any]] = []

    for provider in requested_providers:
        sync_function = MONTHLY_METADATA_PROVIDERS[provider]

        stage = _run_stage(
            db,
            f"metadata:{provider}",
            lambda fn=sync_function: fn(db=db),
            source_name="Official AMC Factsheet",
            source_type="AMC_FACTSHEET",
            provider_key=provider,
        )
        stages.append(stage)

    return {
        "pipeline": "MONTHLY_FUND_PIPELINE",
        "status": "SUCCESS" if _pipeline_succeeded(stages) else "PARTIAL_FAILURE",
        "started_at": pipeline_started_at,
        "completed_at": _utc_now_iso(),
        "providers_requested": requested_providers,
        "stages": stages,
        "data_health": get_fund_data_health(db=db),
    }


def _count_present(db: Session, column) -> int:
    return (
        db.query(func.count(InvestmentProduct.id))
        .filter(
            InvestmentProduct.is_active == True,
            column.isnot(None),
        )
        .scalar()
        or 0
    )


def _count_positive(db: Session, column) -> int:
    return (
        db.query(func.count(InvestmentProduct.id))
        .filter(
            InvestmentProduct.is_active == True,
            column.isnot(None),
            column > 0,
        )
        .scalar()
        or 0
    )


def _percentage(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((value / total) * 100, 2)


def get_fund_data_health(db: Session) -> dict[str, Any]:
    """
    Database-only coverage/freshness snapshot. Safe to run frequently.
    """
    active_total = (
        db.query(func.count(InvestmentProduct.id))
        .filter(InvestmentProduct.is_active == True)
        .scalar()
        or 0
    )

    amfi_mapped = (
        db.query(func.count(InvestmentProduct.id))
        .filter(
            InvestmentProduct.is_active == True,
            InvestmentProduct.scheme_code.isnot(None),
        )
        .scalar()
        or 0
    )

    latest_nav_date = (
        db.query(func.max(InvestmentProduct.nav_date))
        .filter(InvestmentProduct.is_active == True)
        .scalar()
    )

    nav_present = _count_positive(db, InvestmentProduct.nav)
    benchmark_present = _count_present(db, InvestmentProduct.benchmark)
    aum_present = _count_present(db, InvestmentProduct.aum)
    expense_ratio_present = _count_positive(db, InvestmentProduct.expense_ratio)
    fund_manager_present = _count_present(db, InvestmentProduct.fund_manager)
    launch_date_present = _count_present(db, InvestmentProduct.launch_date)

    allocation_present = (
        db.query(func.count(InvestmentProduct.id))
        .filter(
            InvestmentProduct.is_active == True,
            (
                InvestmentProduct.equity_percentage.isnot(None)
                | InvestmentProduct.debt_percentage.isnot(None)
                | InvestmentProduct.cash_percentage.isnot(None)
            ),
        )
        .scalar()
        or 0
    )

    market_cap_present = (
        db.query(func.count(InvestmentProduct.id))
        .filter(
            InvestmentProduct.is_active == True,
            (
                InvestmentProduct.large_cap_percentage.isnot(None)
                | InvestmentProduct.mid_cap_percentage.isnot(None)
                | InvestmentProduct.small_cap_percentage.isnot(None)
            ),
        )
        .scalar()
        or 0
    )

    returns_present = (
        db.query(func.count(InvestmentProduct.id))
        .filter(
            InvestmentProduct.is_active == True,
            (
                (InvestmentProduct.return_1y != 0)
                | (InvestmentProduct.return_3y != 0)
                | (InvestmentProduct.return_5y != 0)
            ),
        )
        .scalar()
        or 0
    )

    fund_form_present = (
        db.query(func.count(InvestmentProduct.id))
        .filter(
            InvestmentProduct.is_active == True,
            InvestmentProduct.fund_status.isnot(None),
            InvestmentProduct.fund_status != "UNRATED",
        )
        .scalar()
        or 0
    )

    status_rows = (
        db.query(
            InvestmentProduct.fund_status,
            func.count(InvestmentProduct.id),
        )
        .filter(InvestmentProduct.is_active == True)
        .group_by(InvestmentProduct.fund_status)
        .all()
    )

    status_distribution = {
        (status or "NULL"): count
        for status, count in status_rows
    }

    latest_nav_age_days = None
    if latest_nav_date:
        latest_nav_age_days = (date.today() - latest_nav_date).days

    return {
        "checked_at": _utc_now_iso(),
        "active_products": active_total,
        "amfi_mapped": {
            "count": amfi_mapped,
            "coverage_pct": _percentage(amfi_mapped, active_total),
        },
        "nav": {
            "count": nav_present,
            "coverage_pct": _percentage(nav_present, active_total),
            "latest_nav_date": latest_nav_date.isoformat() if latest_nav_date else None,
            "latest_nav_age_days": latest_nav_age_days,
        },
        "metadata": {
            "benchmark": {
                "count": benchmark_present,
                "coverage_pct": _percentage(benchmark_present, active_total),
            },
            "expense_ratio": {
                "count": expense_ratio_present,
                "coverage_pct": _percentage(expense_ratio_present, active_total),
            },
            "aum": {
                "count": aum_present,
                "coverage_pct": _percentage(aum_present, active_total),
            },
            "fund_manager": {
                "count": fund_manager_present,
                "coverage_pct": _percentage(fund_manager_present, active_total),
            },
            "launch_date": {
                "count": launch_date_present,
                "coverage_pct": _percentage(launch_date_present, active_total),
            },
            "asset_allocation": {
                "count": allocation_present,
                "coverage_pct": _percentage(allocation_present, active_total),
            },
            "market_cap_allocation": {
                "count": market_cap_present,
                "coverage_pct": _percentage(market_cap_present, active_total),
            },
        },
        "analytics": {
            "returns": {
                "count": returns_present,
                "coverage_pct": _percentage(returns_present, active_total),
            },
            "fund_form": {
                "count": fund_form_present,
                "coverage_pct": _percentage(fund_form_present, active_total),
            },
            "status_distribution": status_distribution,
        },
    }

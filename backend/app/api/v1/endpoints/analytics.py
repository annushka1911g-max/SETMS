"""SETMS — Analytics endpoints."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import CurrentUser
from app.db.database import get_db
from app.models.emergency import Emergency
from app.models.signal import SignalEvent
from app.models.corridor import Corridor
from app.models.enums import EmergencyStatus, EmergencySeverity

router = APIRouter()


@router.get("/summary")
async def analytics_summary(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    total_emergencies = await db.scalar(select(func.count(Emergency.id)))
    completed = await db.scalar(select(func.count(Emergency.id)).where(Emergency.status == EmergencyStatus.COMPLETED))
    avg_duration = await db.scalar(
        select(func.avg(Emergency.final_duration_minutes)).where(
            Emergency.final_duration_minutes.is_not(None)
        )
    )
    # Estimated time saved: sum(baseline_eta - final_duration) for completed emergencies
    # Metric definition: baseline_eta = free-flow ETA estimate at emergency creation (simulated)
    # final_duration = observed journey duration in simulation
    # Result is labeled "simulated_estimate"
    time_saved_result = await db.scalar(
        select(func.sum(Emergency.baseline_eta_minutes - Emergency.final_duration_minutes)).where(
            Emergency.status == EmergencyStatus.COMPLETED,
            Emergency.baseline_eta_minutes.is_not(None),
            Emergency.final_duration_minutes.is_not(None),
            Emergency.baseline_eta_minutes > Emergency.final_duration_minutes,
        )
    )
    return {
        "total_emergencies": total_emergencies or 0,
        "completed_emergencies": completed or 0,
        "avg_journey_duration_minutes": round(float(avg_duration), 2) if avg_duration else None,
        "estimated_time_saved_minutes": {
            "value": round(float(time_saved_result), 2) if time_saved_result else 0.0,
            "label": "simulated_estimate",
            "definition": (
                "Sum of (baseline_eta_minutes - final_duration_minutes) for completed emergencies. "
                "baseline_eta = free-flow route estimate at emergency creation (simulated). "
                "This metric is simulated and does not represent validated real-world performance."
            ),
        },
    }


@router.get("/emergencies")
async def analytics_emergencies(
    current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, ge=1, le=365),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(Emergency.created_at).label("date"),
            Emergency.severity,
            func.count(Emergency.id).label("count"),
        ).where(Emergency.created_at >= since)
        .group_by(func.date(Emergency.created_at), Emergency.severity)
        .order_by(func.date(Emergency.created_at))
    )
    rows = result.all()
    return {"data": [{"date": str(r.date), "severity": r.severity, "count": r.count} for r in rows]}


@router.get("/signals")
async def analytics_signals(
    current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(7, ge=1, le=90),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(SignalEvent.occurred_at).label("date"),
            SignalEvent.trigger,
            func.count(SignalEvent.id).label("count"),
        ).where(SignalEvent.occurred_at >= since)
        .group_by(func.date(SignalEvent.occurred_at), SignalEvent.trigger)
        .order_by(func.date(SignalEvent.occurred_at))
    )
    rows = result.all()
    return {"data": [{"date": str(r.date), "trigger": r.trigger, "count": r.count} for r in rows]}


@router.get("/performance")
async def analytics_performance(
    current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)],
):
    severity_counts = await db.execute(
        select(Emergency.severity, func.count(Emergency.id).label("count"))
        .group_by(Emergency.severity)
    )
    return {
        "severity_distribution": [
            {"severity": r.severity, "count": r.count} for r in severity_counts.all()
        ]
    }

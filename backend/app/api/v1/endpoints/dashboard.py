"""
SETMS — Dashboard summary and activity endpoints.
GET /api/v1/dashboard/summary
GET /api/v1/dashboard/activity
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.database import get_db
from app.models.ambulance import Ambulance
from app.models.corridor import Corridor
from app.models.emergency import Emergency
from app.models.hospital import Hospital
from app.models.signal import TrafficSignal
from app.models.enums import (
    AmbulanceStatus, CorridorStatus, EmergencyStatus, SignalStatus
)

router = APIRouter()


@router.get("/summary", summary="Dashboard summary statistics")
async def dashboard_summary(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Returns real-time counts and statistics for the main dashboard.
    All values are fetched from the database; no values are hardcoded.
    """
    # Active ambulances (en-route or transporting)
    active_ambulances = await db.scalar(
        select(func.count(Ambulance.id)).where(
            Ambulance.status.in_([
                AmbulanceStatus.EN_ROUTE,
                AmbulanceStatus.AT_SCENE,
                AmbulanceStatus.TRANSPORTING,
            ]),
            Ambulance.is_active == True,
        )
    )

    # Total registered ambulances
    total_ambulances = await db.scalar(
        select(func.count(Ambulance.id)).where(Ambulance.is_active == True)
    )

    # Active emergencies
    active_emergencies = await db.scalar(
        select(func.count(Emergency.id)).where(
            Emergency.status == EmergencyStatus.ACTIVE
        )
    )

    # Total emergencies today
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    emergencies_today = await db.scalar(
        select(func.count(Emergency.id)).where(
            Emergency.created_at >= today_start
        )
    )

    # Active corridors
    active_corridors = await db.scalar(
        select(func.count(Corridor.id)).where(
            Corridor.status == CorridorStatus.ACTIVE
        )
    )

    # Total signals
    total_signals = await db.scalar(
        select(func.count(TrafficSignal.id)).where(TrafficSignal.is_active == True)
    )
    signals_in_emergency = await db.scalar(
        select(func.count(TrafficSignal.id)).where(
            TrafficSignal.status == SignalStatus.EMERGENCY_OVERRIDE
        )
    )

    # Hospitals ready
    hospitals_ready = await db.scalar(
        select(func.count(Hospital.id)).where(
            Hospital.is_ready == True,
            Hospital.is_active == True,
        )
    )
    hospitals_total = await db.scalar(
        select(func.count(Hospital.id)).where(Hospital.is_active == True)
    )

    # Average journey duration for completed emergencies (last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    avg_duration = await db.scalar(
        select(func.avg(Emergency.final_duration_minutes)).where(
            Emergency.status == EmergencyStatus.COMPLETED,
            Emergency.completed_at >= seven_days_ago,
            Emergency.final_duration_minutes.is_not(None),
        )
    )

    # Estimated time saved (sum of baseline_eta - final_duration for completed emergencies)
    # This is explicitly labeled as simulated/estimated in the API response
    time_saved_result = await db.execute(
        select(
            func.sum(Emergency.baseline_eta_minutes - Emergency.final_duration_minutes)
        ).where(
            Emergency.status == EmergencyStatus.COMPLETED,
            Emergency.baseline_eta_minutes.is_not(None),
            Emergency.final_duration_minutes.is_not(None),
            Emergency.baseline_eta_minutes > Emergency.final_duration_minutes,
        )
    )
    total_time_saved = time_saved_result.scalar() or 0.0

    return {
        "ambulances": {
            "total": total_ambulances or 0,
            "active": active_ambulances or 0,
            "available": (total_ambulances or 0) - (active_ambulances or 0),
        },
        "emergencies": {
            "active": active_emergencies or 0,
            "today": emergencies_today or 0,
        },
        "corridors": {
            "active": active_corridors or 0,
        },
        "signals": {
            "total": total_signals or 0,
            "in_emergency_override": signals_in_emergency or 0,
        },
        "hospitals": {
            "total": hospitals_total or 0,
            "ready": hospitals_ready or 0,
        },
        "analytics": {
            "avg_journey_duration_minutes_7d": round(float(avg_duration), 1) if avg_duration else None,
            # Note: "time saved" compares simulated baseline ETA vs actual journey duration.
            # This is an estimate, not a validated real-world metric.
            "estimated_time_saved_minutes_label": "simulated_estimate",
            "estimated_time_saved_minutes_total": round(float(total_time_saved), 1),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/activity", summary="Recent system activity feed")
async def dashboard_activity(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 20,
):
    """Returns the most recent emergency and signal events."""
    from app.models.signal import SignalEvent
    from sqlalchemy.orm import selectinload

    # Recent emergencies
    emergency_result = await db.execute(
        select(Emergency)
        .order_by(Emergency.created_at.desc())
        .limit(10)
    )
    emergencies = emergency_result.scalars().all()

    # Recent signal events
    event_result = await db.execute(
        select(SignalEvent)
        .order_by(SignalEvent.occurred_at.desc())
        .limit(10)
    )
    signal_events = event_result.scalars().all()

    activities = []
    for e in emergencies:
        activities.append({
            "type": "emergency",
            "id": e.id,
            "reference_code": e.reference_code,
            "severity": e.severity,
            "status": e.status,
            "timestamp": e.created_at.isoformat(),
        })

    for ev in signal_events:
        activities.append({
            "type": "signal_event",
            "id": ev.id,
            "signal_id": ev.signal_id,
            "from_phase": ev.from_phase,
            "to_phase": ev.to_phase,
            "trigger": ev.trigger,
            "timestamp": ev.occurred_at.isoformat(),
        })

    # Sort combined list by timestamp descending
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"activities": activities[:limit], "count": len(activities[:limit])}

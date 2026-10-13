"""
SETMS — Traffic Signal endpoints.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import CurrentUser, require_roles
from app.db.database import get_db
from app.models.signal import TrafficSignal, SignalEvent
from app.models.enums import SignalMode, SignalPhase, SignalStatus, UserRole

router = APIRouter()


class SignalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    intersection_name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    approach_directions: str = "N,S"
    green_duration_sec: int = Field(default=30, ge=5, le=300)
    yellow_duration_sec: int = Field(default=5, ge=3, le=30)
    red_duration_sec: int = Field(default=35, ge=5, le=300)


class SignalModeRequest(BaseModel):
    mode: SignalMode
    reason: Optional[str] = None


class SignalOut(BaseModel):
    id: str
    name: str
    intersection_name: str
    latitude: float
    longitude: float
    status: SignalStatus
    current_phase: SignalPhase
    current_mode: SignalMode
    approach_directions: str
    green_duration_sec: int
    yellow_duration_sec: int
    red_duration_sec: int
    road_node_id: Optional[str]
    device_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


@router.get("", response_model=dict)
async def list_signals(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0, limit: int = Query(100, le=500),
):
    total = await db.scalar(select(func.count(TrafficSignal.id)).where(TrafficSignal.is_active == True))
    result = await db.execute(select(TrafficSignal).where(TrafficSignal.is_active == True).offset(skip).limit(limit))
    signals = result.scalars().all()
    return {"items": [SignalOut.model_validate(s) for s in signals], "total": total}


@router.post("", response_model=SignalOut, status_code=201,
             dependencies=[Depends(require_roles(UserRole.ADMIN))])
async def create_signal(body: SignalCreate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    signal = TrafficSignal(**body.model_dump())
    db.add(signal)
    await db.flush()
    return SignalOut.model_validate(signal)


@router.get("/{signal_id}", response_model=SignalOut)
async def get_signal(signal_id: str, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(TrafficSignal).where(TrafficSignal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found.")
    return SignalOut.model_validate(signal)


@router.get("/{signal_id}/events", response_model=dict)
async def get_signal_events(
    signal_id: str, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, le=200),
):
    result = await db.execute(
        select(SignalEvent).where(SignalEvent.signal_id == signal_id)
        .order_by(SignalEvent.occurred_at.desc()).limit(limit)
    )
    events = result.scalars().all()
    return {"items": [
        {"id": e.id, "from_phase": e.from_phase, "to_phase": e.to_phase,
         "trigger": e.trigger, "occurred_at": e.occurred_at.isoformat()}
        for e in events
    ], "count": len(events)}


@router.post("/{signal_id}/mode", response_model=SignalOut,
             dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TRAFFIC_OPERATOR))])
async def set_signal_mode(
    signal_id: str, body: SignalModeRequest, current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(TrafficSignal).where(TrafficSignal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found.")

    old_mode = signal.current_mode
    signal.current_mode = body.mode
    if body.mode == SignalMode.NORMAL:
        signal.status = SignalStatus.OPERATIONAL
    elif body.mode == SignalMode.EMERGENCY:
        signal.status = SignalStatus.EMERGENCY_OVERRIDE

    event = SignalEvent(
        signal_id=signal_id,
        from_phase=signal.current_phase,
        to_phase=signal.current_phase,
        from_mode=old_mode,
        to_mode=body.mode,
        trigger="OPERATOR_OVERRIDE",
        triggered_by_user_id=current_user.id,
        notes=body.reason,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.flush()
    return SignalOut.model_validate(signal)

"""
SETMS — Corridor planning and approval endpoints.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import CurrentUser, require_roles
from app.db.database import get_db
from app.models.corridor import Corridor
from app.models.emergency import Emergency
from app.models.enums import CorridorStatus, EmergencyStatus, UserRole

router = APIRouter()


class CorridorPlanRequest(BaseModel):
    emergency_id: str
    # Route provided as ordered list of signal IDs to include in the corridor
    signal_ids: list[str] = []


class CorridorOut(BaseModel):
    id: str
    emergency_id: str
    status: CorridorStatus
    route_json: Optional[str]
    total_distance_meters: Optional[float]
    estimated_duration_seconds: Optional[float]
    proposed_by_user_id: Optional[str]
    approved_by_user_id: Optional[str]
    approved_at: Optional[datetime]
    activated_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    expires_at: Optional[datetime]
    conflict_notes: Optional[str]
    cancel_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


@router.post("/plan", response_model=CorridorOut, status_code=201, summary="Propose a green corridor")
async def plan_corridor(
    body: CorridorPlanRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Creates a PROPOSED corridor for operator review.
    Full route optimization is implemented in Milestone 5/6.
    Currently stores the proposed signal sequence.
    """
    result = await db.execute(select(Emergency).where(Emergency.id == body.emergency_id))
    emergency = result.scalar_one_or_none()
    if not emergency:
        raise HTTPException(status_code=404, detail="Emergency not found.")
    if emergency.status not in [EmergencyStatus.PENDING, EmergencyStatus.ACTIVE]:
        raise HTTPException(status_code=400, detail="Emergency is not active or pending.")

    # Check for existing active/proposed corridor
    existing = await db.execute(
        select(Corridor).where(
            Corridor.emergency_id == body.emergency_id,
            Corridor.status.in_([CorridorStatus.PROPOSED, CorridorStatus.APPROVED, CorridorStatus.ACTIVE]),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An active corridor already exists for this emergency.")

    import json
    corridor = Corridor(
        emergency_id=body.emergency_id,
        status=CorridorStatus.PROPOSED,
        route_json=json.dumps({"signal_ids": body.signal_ids}),
        proposed_by_user_id=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.add(corridor)
    await db.flush()
    return CorridorOut.model_validate(corridor)


@router.get("", response_model=dict, summary="List corridors")
async def list_corridors(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Optional[CorridorStatus] = Query(None, alias="status"),
    skip: int = 0, limit: int = Query(50, le=200),
):
    q = select(Corridor)
    if status_filter:
        q = q.where(Corridor.status == status_filter)
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.offset(skip).limit(limit).order_by(Corridor.created_at.desc()))
    corridors = result.scalars().all()
    return {"items": [CorridorOut.model_validate(c) for c in corridors], "total": total}


@router.get("/{corridor_id}", response_model=CorridorOut)
async def get_corridor(corridor_id: str, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Corridor).where(Corridor.id == corridor_id))
    corridor = result.scalar_one_or_none()
    if not corridor:
        raise HTTPException(status_code=404, detail="Corridor not found.")
    return CorridorOut.model_validate(corridor)


@router.post("/{corridor_id}/approve", response_model=CorridorOut,
             dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TRAFFIC_OPERATOR))])
async def approve_corridor(
    corridor_id: str, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(Corridor).where(Corridor.id == corridor_id))
    corridor = result.scalar_one_or_none()
    if not corridor:
        raise HTTPException(status_code=404, detail="Corridor not found.")
    if corridor.status != CorridorStatus.PROPOSED:
        raise HTTPException(status_code=400, detail=f"Cannot approve corridor in status '{corridor.status}'.")

    now = datetime.now(timezone.utc)
    corridor.status = CorridorStatus.APPROVED
    corridor.approved_by_user_id = current_user.id
    corridor.approved_at = now
    # Auto-activate on approval (full scheduling logic in Milestone 6)
    corridor.status = CorridorStatus.ACTIVE
    corridor.activated_at = now
    await db.flush()
    return CorridorOut.model_validate(corridor)


@router.post("/{corridor_id}/cancel", response_model=CorridorOut)
async def cancel_corridor(
    corridor_id: str, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(Corridor).where(Corridor.id == corridor_id))
    corridor = result.scalar_one_or_none()
    if not corridor:
        raise HTTPException(status_code=404, detail="Corridor not found.")
    if corridor.status in [CorridorStatus.COMPLETED, CorridorStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail=f"Corridor already in final status '{corridor.status}'.")

    corridor.status = CorridorStatus.CANCELLED
    corridor.cancelled_at = datetime.now(timezone.utc)
    await db.flush()
    return CorridorOut.model_validate(corridor)

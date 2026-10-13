"""
SETMS — Emergency lifecycle endpoints.
"""
from __future__ import annotations

import random
import string
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_roles
from app.db.database import get_db
from app.models.ambulance import Ambulance
from app.models.emergency import Emergency
from app.models.hospital import Hospital
from app.models.enums import (
    AmbulanceStatus, EmergencyStatus, EmergencySeverity, UserRole
)

router = APIRouter()


def _generate_reference_code() -> str:
    """Generate a short, human-readable emergency reference code."""
    prefix = "EMR"
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{suffix}"


class EmergencyCreate(BaseModel):
    ambulance_id: str
    destination_hospital_id: Optional[str] = None
    severity: EmergencySeverity = EmergencySeverity.HIGH
    description: Optional[str] = Field(default=None, max_length=1000)
    origin_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    origin_lng: Optional[float] = Field(default=None, ge=-180, le=180)
    origin_address: Optional[str] = None
    dest_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    dest_lng: Optional[float] = Field(default=None, ge=-180, le=180)


class EmergencyOut(BaseModel):
    id: str
    reference_code: str
    ambulance_id: str
    destination_hospital_id: Optional[str]
    severity: EmergencySeverity
    status: EmergencyStatus
    description: Optional[str]
    origin_lat: Optional[float]
    origin_lng: Optional[float]
    origin_address: Optional[str]
    dest_lat: Optional[float]
    dest_lng: Optional[float]
    activated_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    initial_eta_minutes: Optional[float]
    final_duration_minutes: Optional[float]
    baseline_eta_minutes: Optional[float]
    priority_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=dict, summary="List emergencies")
async def list_emergencies(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Optional[EmergencyStatus] = Query(None, alias="status"),
    severity_filter: Optional[EmergencySeverity] = Query(None, alias="severity"),
    skip: int = 0,
    limit: int = Query(50, le=200),
):
    q = select(Emergency)
    if status_filter:
        q = q.where(Emergency.status == status_filter)
    if severity_filter:
        q = q.where(Emergency.severity == severity_filter)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.offset(skip).limit(limit).order_by(Emergency.created_at.desc()))
    emergencies = result.scalars().all()

    return {
        "items": [EmergencyOut.model_validate(e) for e in emergencies],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post(
    "",
    response_model=EmergencyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new emergency request",
)
async def create_emergency(
    body: EmergencyCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Validate ambulance exists
    ambulance_result = await db.execute(
        select(Ambulance).where(Ambulance.id == body.ambulance_id)
    )
    ambulance = ambulance_result.scalar_one_or_none()
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found.")
    if not ambulance.is_active:
        raise HTTPException(status_code=400, detail="Ambulance is not active.")

    # Validate hospital if provided
    if body.destination_hospital_id:
        hospital_result = await db.execute(
            select(Hospital).where(Hospital.id == body.destination_hospital_id)
        )
        if not hospital_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Destination hospital not found.")

    # Check no active emergency for this ambulance
    existing = await db.execute(
        select(Emergency).where(
            Emergency.ambulance_id == body.ambulance_id,
            Emergency.status.in_([EmergencyStatus.PENDING, EmergencyStatus.ACTIVE]),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This ambulance already has an active or pending emergency.",
        )

    emergency = Emergency(
        reference_code=_generate_reference_code(),
        ambulance_id=body.ambulance_id,
        destination_hospital_id=body.destination_hospital_id,
        severity=body.severity,
        description=body.description,
        origin_lat=body.origin_lat,
        origin_lng=body.origin_lng,
        origin_address=body.origin_address,
        dest_lat=body.dest_lat,
        dest_lng=body.dest_lng,
        created_by_user_id=current_user.id,
        status=EmergencyStatus.PENDING,
    )
    db.add(emergency)
    await db.flush()
    return EmergencyOut.model_validate(emergency)


@router.get("/{emergency_id}", response_model=EmergencyOut, summary="Get emergency by ID")
async def get_emergency(
    emergency_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Emergency).where(Emergency.id == emergency_id))
    emergency = result.scalar_one_or_none()
    if not emergency:
        raise HTTPException(status_code=404, detail="Emergency not found.")
    return EmergencyOut.model_validate(emergency)


@router.post("/{emergency_id}/activate", response_model=EmergencyOut, summary="Activate emergency")
async def activate_emergency(
    emergency_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Emergency).where(Emergency.id == emergency_id))
    emergency = result.scalar_one_or_none()
    if not emergency:
        raise HTTPException(status_code=404, detail="Emergency not found.")
    if emergency.status != EmergencyStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot activate emergency in status '{emergency.status}'.",
        )
    emergency.status = EmergencyStatus.ACTIVE
    emergency.activated_at = datetime.now(timezone.utc)

    # Update ambulance status
    ambulance_result = await db.execute(
        select(Ambulance).where(Ambulance.id == emergency.ambulance_id)
    )
    ambulance = ambulance_result.scalar_one_or_none()
    if ambulance:
        ambulance.status = AmbulanceStatus.EN_ROUTE

    await db.flush()
    return EmergencyOut.model_validate(emergency)


@router.post("/{emergency_id}/complete", response_model=EmergencyOut, summary="Complete emergency")
async def complete_emergency(
    emergency_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Emergency).where(Emergency.id == emergency_id))
    emergency = result.scalar_one_or_none()
    if not emergency:
        raise HTTPException(status_code=404, detail="Emergency not found.")
    if emergency.status != EmergencyStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete emergency in status '{emergency.status}'.",
        )

    now = datetime.now(timezone.utc)
    emergency.status = EmergencyStatus.COMPLETED
    emergency.completed_at = now

    if emergency.activated_at:
        duration = (now - emergency.activated_at).total_seconds() / 60
        emergency.final_duration_minutes = round(duration, 2)

    # Return ambulance to available
    ambulance_result = await db.execute(
        select(Ambulance).where(Ambulance.id == emergency.ambulance_id)
    )
    ambulance = ambulance_result.scalar_one_or_none()
    if ambulance:
        ambulance.status = AmbulanceStatus.AVAILABLE

    await db.flush()
    return EmergencyOut.model_validate(emergency)


@router.post("/{emergency_id}/cancel", response_model=EmergencyOut, summary="Cancel emergency")
async def cancel_emergency(
    emergency_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Emergency).where(Emergency.id == emergency_id))
    emergency = result.scalar_one_or_none()
    if not emergency:
        raise HTTPException(status_code=404, detail="Emergency not found.")
    if emergency.status in [EmergencyStatus.COMPLETED, EmergencyStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Emergency already in final status '{emergency.status}'.",
        )

    emergency.status = EmergencyStatus.CANCELLED
    emergency.cancelled_at = datetime.now(timezone.utc)

    ambulance_result = await db.execute(
        select(Ambulance).where(Ambulance.id == emergency.ambulance_id)
    )
    ambulance = ambulance_result.scalar_one_or_none()
    if ambulance and ambulance.status == AmbulanceStatus.EN_ROUTE:
        ambulance.status = AmbulanceStatus.AVAILABLE

    await db.flush()
    return EmergencyOut.model_validate(emergency)

"""
SETMS — Ambulance CRUD and location update endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_roles
from app.db.database import get_db
from app.models.ambulance import Ambulance, AmbulanceLocation
from app.models.enums import AmbulanceStatus, UserRole

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AmbulanceCreate(BaseModel):
    registration_number: str = Field(min_length=3, max_length=32)
    call_sign: str = Field(min_length=1, max_length=64)
    vehicle_type: str = "Type-B"
    notes: Optional[str] = None


class AmbulancePatch(BaseModel):
    call_sign: Optional[str] = None
    vehicle_type: Optional[str] = None
    status: Optional[AmbulanceStatus] = None
    driver_user_id: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class LocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed_kmh: Optional[float] = Field(default=None, ge=0, le=300)
    heading_degrees: Optional[float] = Field(default=None, ge=0, le=360)
    accuracy_meters: Optional[float] = None
    source: str = "SIMULATED"  # DEVICE_GPS, SIMULATED, MANUALLY_ENTERED


class AmbulanceOut(BaseModel):
    id: str
    registration_number: str
    call_sign: str
    vehicle_type: str
    status: AmbulanceStatus
    current_lat: Optional[float]
    current_lng: Optional[float]
    current_speed_kmh: Optional[float]
    location_updated_at: Optional[datetime]
    driver_user_id: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=dict, summary="List ambulances")
async def list_ambulances(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Optional[AmbulanceStatus] = Query(None, alias="status"),
    active_only: bool = True,
    skip: int = 0,
    limit: int = Query(50, le=200),
):
    q = select(Ambulance)
    if active_only:
        q = q.where(Ambulance.is_active == True)
    if status_filter:
        q = q.where(Ambulance.status == status_filter)

    count_q = select(func.count()).select_from(q.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(q.offset(skip).limit(limit).order_by(Ambulance.call_sign))
    ambulances = result.scalars().all()

    return {
        "items": [AmbulanceOut.model_validate(a) for a in ambulances],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post(
    "",
    response_model=AmbulanceOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
    summary="Register a new ambulance",
)
async def create_ambulance(
    body: AmbulanceCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    existing = await db.execute(
        select(Ambulance).where(Ambulance.registration_number == body.registration_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ambulance with this registration number already exists.",
        )

    ambulance = Ambulance(**body.model_dump())
    db.add(ambulance)
    await db.flush()
    return AmbulanceOut.model_validate(ambulance)


@router.get("/{ambulance_id}", response_model=AmbulanceOut, summary="Get ambulance by ID")
async def get_ambulance(
    ambulance_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Ambulance).where(Ambulance.id == ambulance_id))
    ambulance = result.scalar_one_or_none()
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found.")
    return AmbulanceOut.model_validate(ambulance)


@router.patch(
    "/{ambulance_id}",
    response_model=AmbulanceOut,
    summary="Update ambulance details",
)
async def update_ambulance(
    ambulance_id: str,
    body: AmbulancePatch,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Ambulance).where(Ambulance.id == ambulance_id))
    ambulance = result.scalar_one_or_none()
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found.")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ambulance, key, value)
    await db.flush()
    return AmbulanceOut.model_validate(ambulance)


@router.post(
    "/{ambulance_id}/location",
    status_code=status.HTTP_200_OK,
    summary="Update ambulance GPS location",
)
async def update_location(
    ambulance_id: str,
    body: LocationUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Ambulance).where(Ambulance.id == ambulance_id))
    ambulance = result.scalar_one_or_none()
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found.")

    now = datetime.now(timezone.utc)

    # Update denormalized current location
    ambulance.current_lat = body.latitude
    ambulance.current_lng = body.longitude
    ambulance.current_speed_kmh = body.speed_kmh
    ambulance.location_updated_at = now

    # Persist to time-series table
    loc = AmbulanceLocation(
        ambulance_id=ambulance_id,
        latitude=body.latitude,
        longitude=body.longitude,
        speed_kmh=body.speed_kmh,
        heading_degrees=body.heading_degrees,
        accuracy_meters=body.accuracy_meters,
        source=body.source,
        recorded_at=now,
    )
    db.add(loc)
    await db.flush()

    return {"status": "location_updated", "ambulance_id": ambulance_id, "recorded_at": now.isoformat()}


@router.post(
    "/{ambulance_id}/heartbeat",
    status_code=status.HTTP_200_OK,
    summary="Ambulance device heartbeat",
)
async def heartbeat(
    ambulance_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Ambulance).where(Ambulance.id == ambulance_id))
    ambulance = result.scalar_one_or_none()
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found.")
    ambulance.location_updated_at = datetime.now(timezone.utc)
    await db.flush()
    return {"status": "ok", "ambulance_id": ambulance_id}

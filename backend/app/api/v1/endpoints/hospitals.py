"""SETMS — Hospital endpoints."""
from __future__ import annotations
from datetime import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import CurrentUser, require_roles
from app.db.database import get_db
from app.models.hospital import Hospital, HospitalNotification
from app.models.enums import UserRole

router = APIRouter()


class HospitalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str = ""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    emergency_bays_total: int = Field(default=5, ge=1)
    emergency_bays_available: int = Field(default=5, ge=0)


class HospitalReadinessPatch(BaseModel):
    is_ready: bool
    emergency_bays_available: Optional[int] = None
    readiness_note: Optional[str] = None


class HospitalOut(BaseModel):
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    contact_phone: Optional[str]
    contact_email: Optional[str]
    emergency_bays_total: int
    emergency_bays_available: int
    is_ready: bool
    readiness_note: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


@router.get("", response_model=dict)
async def list_hospitals(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)],
                         skip: int = 0, limit: int = Query(50, le=200)):
    total = await db.scalar(select(func.count(Hospital.id)).where(Hospital.is_active == True))
    result = await db.execute(select(Hospital).where(Hospital.is_active == True).offset(skip).limit(limit))
    hospitals = result.scalars().all()
    return {"items": [HospitalOut.model_validate(h) for h in hospitals], "total": total}


@router.post("", response_model=HospitalOut, status_code=201,
             dependencies=[Depends(require_roles(UserRole.ADMIN))])
async def create_hospital(body: HospitalCreate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    hospital = Hospital(**body.model_dump())
    db.add(hospital)
    await db.flush()
    return HospitalOut.model_validate(hospital)


@router.get("/incoming", response_model=dict, summary="Hospitals with incoming ambulances")
async def incoming_ambulances(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    from app.models.emergency import Emergency
    from app.models.enums import EmergencyStatus
    result = await db.execute(
        select(Hospital, Emergency).join(
            Emergency, Emergency.destination_hospital_id == Hospital.id
        ).where(Emergency.status == EmergencyStatus.ACTIVE)
    )
    rows = result.all()
    return {"items": [
        {"hospital": HospitalOut.model_validate(h), "emergency_id": e.id,
         "severity": e.severity, "reference_code": e.reference_code}
        for h, e in rows
    ]}


@router.patch("/{hospital_id}/readiness", response_model=HospitalOut)
async def update_readiness(
    hospital_id: str, body: HospitalReadinessPatch, current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Hospital).where(Hospital.id == hospital_id))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found.")
    hospital.is_ready = body.is_ready
    if body.emergency_bays_available is not None:
        hospital.emergency_bays_available = body.emergency_bays_available
    if body.readiness_note is not None:
        hospital.readiness_note = body.readiness_note
    await db.flush()
    return HospitalOut.model_validate(hospital)

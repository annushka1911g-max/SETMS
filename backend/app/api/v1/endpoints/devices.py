"""SETMS — Device management endpoints."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import CurrentUser
from app.db.database import get_db
from app.models.device import Device, DeviceHeartbeat
from app.models.enums import DeviceConnectivity, DeviceType

router = APIRouter()

OFFLINE_THRESHOLD_MINUTES = 5


class DeviceOut(BaseModel):
    id: str
    name: str
    device_type: DeviceType
    firmware_version: Optional[str]
    mqtt_client_id: Optional[str]
    connectivity: DeviceConnectivity
    last_seen_at: Optional[datetime]
    ip_address: Optional[str]
    is_simulated: bool
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


@router.get("", response_model=dict)
async def list_devices(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)],
                       skip: int = 0, limit: int = Query(50, le=200)):
    total = await db.scalar(select(func.count(Device.id)).where(Device.is_active == True))
    result = await db.execute(select(Device).where(Device.is_active == True).offset(skip).limit(limit))
    devices = result.scalars().all()
    return {"items": [DeviceOut.model_validate(d) for d in devices], "total": total}


@router.get("/{device_id}/status")
async def get_device_status(device_id: str, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")

    # Determine if device is stale
    threshold = datetime.now(timezone.utc) - timedelta(minutes=OFFLINE_THRESHOLD_MINUTES)
    is_stale = device.last_seen_at is None or device.last_seen_at < threshold

    # Latest heartbeat
    hb_result = await db.execute(
        select(DeviceHeartbeat).where(DeviceHeartbeat.device_id == device_id)
        .order_by(DeviceHeartbeat.received_at.desc()).limit(1)
    )
    latest_heartbeat = hb_result.scalar_one_or_none()

    return {
        "device": DeviceOut.model_validate(device),
        "is_stale": is_stale,
        "latest_heartbeat": {
            "received_at": latest_heartbeat.received_at.isoformat() if latest_heartbeat else None,
            "uptime_seconds": latest_heartbeat.uptime_seconds if latest_heartbeat else None,
        } if latest_heartbeat else None,
    }

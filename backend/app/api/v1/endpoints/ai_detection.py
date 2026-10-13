"""
SETMS — AI Detection endpoints.
Proxies to the ai-engine service or uses simulation mode.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import CurrentUser
from app.core.config import get_settings
from app.db.database import get_db
from app.models.detection import VehicleDetection, TrafficDensitySnapshot
from app.models.enums import DataSource, DensityLevel

router = APIRouter()

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class DetectionOut(BaseModel):
    id: str
    signal_id: Optional[str]
    vehicle_class: str
    confidence: float
    is_ambulance_candidate: bool
    source: DataSource
    detected_at: datetime
    model_config = {"from_attributes": True}


class DensityOut(BaseModel):
    id: str
    signal_id: Optional[str]
    vehicle_count: int
    density_level: DensityLevel
    data_source: DataSource
    captured_at: datetime
    model_config = {"from_attributes": True}


@router.post("/detect", response_model=dict, summary="Submit image for vehicle detection")
async def detect_vehicles(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    signal_id: Optional[str] = None,
    file: UploadFile = File(None),
):
    """
    Forward an image to the AI engine for YOLO detection.
    Falls back to simulation if AI_SIMULATION_MODE=true or engine is unavailable.
    """
    settings = get_settings()

    if file and file.size and file.size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Upload exceeds 10 MB limit.")

    if settings.ai_simulation_mode or not file:
        # Simulation fallback — generate synthetic detections clearly labeled as SIMULATED
        import random
        now = datetime.now(timezone.utc)
        classes = ["car", "motorcycle", "truck", "bus"]
        detections = []
        for _ in range(random.randint(2, 8)):
            vc = random.choice(classes)
            det = VehicleDetection(
                signal_id=signal_id,
                vehicle_class=vc,
                confidence=round(random.uniform(0.55, 0.97), 3),
                is_ambulance_candidate=vc == "ambulance",
                source=DataSource.SIMULATED,
                detected_at=now,
            )
            db.add(det)
            detections.append(det)
        await db.flush()
        return {
            "mode": "simulated",
            "warning": "Detections are synthetically generated. Not based on real camera data.",
            "count": len(detections),
            "detections": [DetectionOut.model_validate(d) for d in detections],
        }

    # Real AI engine call
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            content = await file.read()
            response = await client.post(
                f"{settings.ai_engine_url}/detect",
                files={"file": (file.filename, content, file.content_type)},
                params={"signal_id": signal_id} if signal_id else {},
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI engine unavailable: {exc}")


@router.get("/detections", response_model=dict)
async def list_detections(
    current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)],
    signal_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    q = select(VehicleDetection)
    if signal_id:
        q = q.where(VehicleDetection.signal_id == signal_id)
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.order_by(VehicleDetection.detected_at.desc()).limit(limit))
    detections = result.scalars().all()
    return {"items": [DetectionOut.model_validate(d) for d in detections], "total": total}


@router.get("/traffic-density", response_model=dict)
async def get_traffic_density(
    current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)],
    signal_id: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
):
    q = select(TrafficDensitySnapshot)
    if signal_id:
        q = q.where(TrafficDensitySnapshot.signal_id == signal_id)
    result = await db.execute(q.order_by(TrafficDensitySnapshot.captured_at.desc()).limit(limit))
    snapshots = result.scalars().all()
    return {"items": [DensityOut.model_validate(s) for s in snapshots], "count": len(snapshots)}

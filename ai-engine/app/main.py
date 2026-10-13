"""
SETMS AI Engine — FastAPI service for YOLO-based vehicle detection.
Milestone 1: Health endpoints and simulation mode.
"""
from __future__ import annotations

import os
import random
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, File, Query, UploadFile
from pydantic import BaseModel

app = FastAPI(
    title="SETMS AI Engine",
    description="Vehicle detection and traffic density estimation service.\n\n"
    "⚠️ When AI_SIMULATION_MODE=true, all detections are synthetically generated "
    "and clearly labeled as SIMULATED. Not based on real camera data.",
    version="1.0.0",
)

AI_SIMULATION_MODE = os.getenv("AI_SIMULATION_MODE", "true").lower() == "true"
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "weights/yolov8n.pt")

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model
    if AI_SIMULATION_MODE:
        return None
    try:
        from ultralytics import YOLO
        _model = YOLO(YOLO_MODEL_PATH)
        return _model
    except Exception as exc:
        print(f"[AI Engine] Could not load YOLO model: {exc}. Falling back to simulation mode.")
        return None


@app.on_event("startup")
async def startup():
    _load_model()


class Detection(BaseModel):
    vehicle_class: str
    confidence: float
    is_ambulance_candidate: bool
    bbox_x: Optional[float] = None
    bbox_y: Optional[float] = None
    bbox_w: Optional[float] = None
    bbox_h: Optional[float] = None
    source: str = "SIMULATED"


class DetectResponse(BaseModel):
    mode: str
    detections: list[Detection]
    count: int
    detected_at: str
    warning: Optional[str] = None


class DensityResponse(BaseModel):
    vehicle_count: int
    density_level: str
    data_source: str
    captured_at: str
    warning: Optional[str] = None


@app.get("/health", summary="Health check")
async def health():
    model_loaded = _model is not None
    return {
        "status": "ok",
        "service": "setms-ai-engine",
        "simulation_mode": AI_SIMULATION_MODE,
        "model_loaded": model_loaded,
        "model_path": YOLO_MODEL_PATH if not AI_SIMULATION_MODE else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/detect", response_model=DetectResponse, summary="Vehicle detection")
async def detect(
    file: UploadFile = File(None),
    signal_id: Optional[str] = Query(None),
):
    """
    Perform vehicle detection on an image.
    In simulation mode, generates synthetic detections labeled as SIMULATED.
    In real mode, runs YOLO inference on the uploaded image.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Check upload size (10 MB limit)
    if file:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            from fastapi import HTTPException
            raise HTTPException(status_code=413, detail="File exceeds 10 MB limit.")

    model = _load_model()

    if model is None or AI_SIMULATION_MODE:
        # Simulation fallback
        classes = ["car", "motorcycle", "truck", "bus", "car", "car", "motorcycle"]
        detections = []
        for _ in range(random.randint(2, 10)):
            vc = random.choice(classes)
            detections.append(Detection(
                vehicle_class=vc,
                confidence=round(random.uniform(0.50, 0.97), 3),
                is_ambulance_candidate=False,
                bbox_x=round(random.uniform(0.05, 0.7), 3),
                bbox_y=round(random.uniform(0.1, 0.6), 3),
                bbox_w=round(random.uniform(0.08, 0.25), 3),
                bbox_h=round(random.uniform(0.06, 0.20), 3),
                source="SIMULATED",
            ))
        return DetectResponse(
            mode="simulation",
            detections=detections,
            count=len(detections),
            detected_at=now,
            warning="Detections are synthetically generated for demonstration. Not based on real camera data.",
        )

    # Real inference
    import cv2
    import numpy as np
    img_array = np.frombuffer(content, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Could not decode image.")

    results = model(img, conf=float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.45")))
    detections = []
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]
            conf = float(box.conf[0])
            x, y, w, h = box.xywhn[0].tolist()
            detections.append(Detection(
                vehicle_class=cls_name,
                confidence=round(conf, 3),
                is_ambulance_candidate=cls_name.lower() in ["ambulance", "emergency"],
                bbox_x=round(x, 4), bbox_y=round(y, 4),
                bbox_w=round(w, 4), bbox_h=round(h, 4),
                source="AI_ESTIMATED",
            ))

    return DetectResponse(mode="inference", detections=detections, count=len(detections), detected_at=now)


@app.post("/density", response_model=DensityResponse, summary="Traffic density estimation")
async def density(file: UploadFile = File(None)):
    """
    Estimate traffic density from an image or generate a simulated snapshot.
    """
    now = datetime.now(timezone.utc).isoformat()
    model = _load_model()

    if model is None or AI_SIMULATION_MODE:
        count = random.randint(3, 25)
        level = "LOW" if count < 8 else "MEDIUM" if count < 16 else "HIGH"
        return DensityResponse(
            vehicle_count=count,
            density_level=level,
            data_source="SIMULATED",
            captured_at=now,
            warning="Traffic density is synthetically simulated. Not based on real camera data.",
        )

    # Real: run detect then count
    detect_result = await detect(file=file)
    count = detect_result.count
    level = "LOW" if count < 8 else "MEDIUM" if count < 16 else "HIGH" if count < 25 else "GRIDLOCK"
    return DensityResponse(
        vehicle_count=count,
        density_level=level,
        data_source="AI_ESTIMATED",
        captured_at=now,
    )

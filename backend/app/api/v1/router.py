"""
SETMS — API v1 Router — aggregates all endpoint modules.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, dashboard, ambulances, emergencies, signals, corridors, hospitals, analytics, devices, ai_detection

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_v1_router.include_router(ambulances.router, prefix="/ambulances", tags=["Ambulances"])
api_v1_router.include_router(emergencies.router, prefix="/emergencies", tags=["Emergencies"])
api_v1_router.include_router(signals.router, prefix="/signals", tags=["Traffic Signals"])
api_v1_router.include_router(corridors.router, prefix="/corridors", tags=["Corridors"])
api_v1_router.include_router(hospitals.router, prefix="/hospitals", tags=["Hospitals"])
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_v1_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_v1_router.include_router(ai_detection.router, prefix="/ai", tags=["AI Detection"])

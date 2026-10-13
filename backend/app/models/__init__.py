"""
SETMS Backend — All SQLAlchemy Models
Import all models here so that Base.metadata is populated before migrations.
"""
from app.models.user import User  # noqa: F401
from app.models.ambulance import Ambulance, AmbulanceLocation  # noqa: F401
from app.models.hospital import Hospital, HospitalNotification  # noqa: F401
from app.models.signal import TrafficSignal, SignalEvent  # noqa: F401
from app.models.road import RoadNode, RoadEdge  # noqa: F401
from app.models.emergency import Emergency  # noqa: F401
from app.models.corridor import Corridor, CorridorSignal  # noqa: F401
from app.models.detection import VehicleDetection, TrafficDensitySnapshot  # noqa: F401
from app.models.device import Device, DeviceHeartbeat  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401

__all__ = [
    "User",
    "Ambulance",
    "AmbulanceLocation",
    "Hospital",
    "HospitalNotification",
    "TrafficSignal",
    "SignalEvent",
    "RoadNode",
    "RoadEdge",
    "Emergency",
    "Corridor",
    "CorridorSignal",
    "VehicleDetection",
    "TrafficDensitySnapshot",
    "Device",
    "DeviceHeartbeat",
    "AuditLog",
]

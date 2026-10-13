"""
SETMS — Shared enumerations used across models and schemas.
"""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    TRAFFIC_OPERATOR = "TRAFFIC_OPERATOR"
    AMBULANCE_DRIVER = "AMBULANCE_DRIVER"
    HOSPITAL_OPERATOR = "HOSPITAL_OPERATOR"
    VIEWER = "VIEWER"


class EmergencySeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"


class EmergencyStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AmbulanceStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    EN_ROUTE = "EN_ROUTE"
    AT_SCENE = "AT_SCENE"
    TRANSPORTING = "TRANSPORTING"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class SignalStatus(str, enum.Enum):
    OPERATIONAL = "OPERATIONAL"
    EMERGENCY_OVERRIDE = "EMERGENCY_OVERRIDE"
    FAULT = "FAULT"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"


class SignalPhase(str, enum.Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    FLASHING_RED = "FLASHING_RED"


class SignalMode(str, enum.Enum):
    NORMAL = "NORMAL"
    EMERGENCY = "EMERGENCY"
    MANUAL = "MANUAL"
    FLASHING = "FLASHING"
    OFF = "OFF"


class CorridorStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class DeviceConnectivity(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class DeviceType(str, enum.Enum):
    ESP32_SIGNAL = "ESP32_SIGNAL"
    RASPBERRY_PI_CAMERA = "RASPBERRY_PI_CAMERA"
    GPS_TRACKER = "GPS_TRACKER"
    SIMULATOR = "SIMULATOR"


class DensityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    GRIDLOCK = "GRIDLOCK"


class DataSource(str, enum.Enum):
    """Clearly identifies the origin of data — never present synthetic data as real."""
    AI_ESTIMATED = "AI_ESTIMATED"
    MANUALLY_ENTERED = "MANUALLY_ENTERED"
    SIMULATED = "SIMULATED"
    DEVICE_REPORTED = "DEVICE_REPORTED"

"""
SETMS — Device and DeviceHeartbeat models (IoT).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import DeviceConnectivity, DeviceType


class Device(UUIDMixin, TimestampMixin, Base):
    """
    Represents an IoT device (ESP32 signal controller, RPi camera, GPS tracker).
    """
    __tablename__ = "devices"

    device_type: Mapped[DeviceType] = mapped_column(
        String(32), nullable=False, default=DeviceType.SIMULATOR
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mqtt_client_id: Mapped[Optional[str]] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )

    connectivity: Mapped[DeviceConnectivity] = mapped_column(
        String(32), nullable=False, default=DeviceConnectivity.UNKNOWN
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Location (if GPS-capable)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    heartbeats: Mapped[list["DeviceHeartbeat"]] = relationship(
        "DeviceHeartbeat", back_populates="device", lazy="noload",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Device {self.name} type={self.device_type} conn={self.connectivity}>"


class DeviceHeartbeat(UUIDMixin, Base):
    """
    Periodic heartbeat record from a device.
    Used to detect offline devices and audit connectivity.
    """
    __tablename__ = "device_heartbeats"

    device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device: Mapped["Device"] = relationship("Device", back_populates="heartbeats")

    firmware_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    uptime_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    free_memory_bytes: Mapped[Optional[int]] = mapped_column(nullable=True)
    signal_strength_dbm: Mapped[Optional[int]] = mapped_column(nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    mqtt_message_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index("ix_device_heartbeats_device_received", "device_id", "received_at"),
    )

"""
SETMS — Ambulance and AmbulanceLocation models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import AmbulanceStatus


class Ambulance(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ambulances"

    registration_number: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    call_sign: Mapped[str] = mapped_column(String(64), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="Type-B"
    )
    status: Mapped[AmbulanceStatus] = mapped_column(
        String(32), nullable=False, default=AmbulanceStatus.AVAILABLE
    )
    # Current location — denormalized for fast reads
    current_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_speed_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Driver user link
    driver_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    driver_user: Mapped[Optional["User"]] = relationship(  # noqa: F821
        "User", foreign_keys=[driver_user_id], lazy="noload"
    )

    notes: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    locations: Mapped[list["AmbulanceLocation"]] = relationship(
        "AmbulanceLocation", back_populates="ambulance", lazy="noload",
        cascade="all, delete-orphan"
    )
    emergencies: Mapped[list["Emergency"]] = relationship(  # noqa: F821
        "Emergency", back_populates="ambulance", lazy="noload"
    )

    __table_args__ = (
        Index("ix_ambulances_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Ambulance {self.call_sign} [{self.registration_number}] status={self.status}>"


class AmbulanceLocation(UUIDMixin, Base):
    """
    Time-series GPS track for an ambulance.
    Each location update is persisted here for history and analytics.
    """
    __tablename__ = "ambulance_locations"

    ambulance_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ambulances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ambulance: Mapped["Ambulance"] = relationship(
        "Ambulance", back_populates="locations"
    )

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    speed_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    heading_degrees: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accuracy_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Source of location: device GPS, simulation, etc.
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="SIMULATED")

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index("ix_ambulance_locations_ambulance_recorded", "ambulance_id", "recorded_at"),
    )

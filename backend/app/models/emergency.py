"""
SETMS — Emergency model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import EmergencySeverity, EmergencyStatus


class Emergency(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "emergencies"

    # Reference code shown to operators
    reference_code: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )

    ambulance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ambulances.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    ambulance: Mapped["Ambulance"] = relationship(  # noqa: F821
        "Ambulance", back_populates="emergencies", lazy="noload"
    )

    destination_hospital_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    destination_hospital: Mapped[Optional["Hospital"]] = relationship(  # noqa: F821
        "Hospital", back_populates="emergencies", lazy="noload"
    )

    # Who created this emergency
    created_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    severity: Mapped[EmergencySeverity] = mapped_column(
        String(32), nullable=False, default=EmergencySeverity.HIGH
    )
    status: Mapped[EmergencyStatus] = mapped_column(
        String(32), nullable=False, default=EmergencyStatus.PENDING
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Origin coordinates (pickup location)
    origin_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    origin_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    origin_address: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Destination coordinates
    dest_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dest_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Lifecycle timestamps
    activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ETA tracking
    initial_eta_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_duration_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Baseline estimate used for "time saved" metric (simulated free-flow ETA)
    baseline_eta_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Priority score (calculated by priority engine)
    priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    corridors: Mapped[list["Corridor"]] = relationship(  # noqa: F821
        "Corridor", back_populates="emergency", lazy="noload"
    )
    hospital_notifications: Mapped[list["HospitalNotification"]] = relationship(  # noqa: F821
        "HospitalNotification",
        primaryjoin="Emergency.id == foreign(HospitalNotification.emergency_id)",
        lazy="noload",
    )

    __table_args__ = (
        Index("ix_emergencies_status_severity", "status", "severity"),
        Index("ix_emergencies_ambulance_status", "ambulance_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Emergency {self.reference_code} severity={self.severity} status={self.status}>"

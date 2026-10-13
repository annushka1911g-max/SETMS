"""
SETMS — Hospital and HospitalNotification models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Hospital(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "hospitals"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)

    # Readiness status: number of available emergency bays
    emergency_bays_total: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    emergency_bays_available: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_ready: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    readiness_note: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    notifications: Mapped[list["HospitalNotification"]] = relationship(
        "HospitalNotification", back_populates="hospital",
        lazy="noload", cascade="all, delete-orphan"
    )
    emergencies: Mapped[list["Emergency"]] = relationship(  # noqa: F821
        "Emergency", back_populates="destination_hospital", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Hospital {self.name}>"


class HospitalNotification(UUIDMixin, Base):
    """Persisted notification sent to a hospital for an incoming emergency."""
    __tablename__ = "hospital_notifications"

    hospital_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hospital: Mapped["Hospital"] = relationship(
        "Hospital", back_populates="notifications"
    )

    emergency_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("emergencies.id", ondelete="SET NULL"), nullable=True, index=True
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    ambulance_eta_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_hospital_notifications_hospital_sent", "hospital_id", "sent_at"),
    )

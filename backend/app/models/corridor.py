"""
SETMS — Corridor and CorridorSignal models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import CorridorStatus, SignalPhase


class Corridor(UUIDMixin, TimestampMixin, Base):
    """
    A planned green corridor — a sequence of intersections with scheduled signal times.
    Corridors go through: PROPOSED → APPROVED → ACTIVE → COMPLETED/CANCELLED.
    """
    __tablename__ = "corridors"

    emergency_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("emergencies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    emergency: Mapped["Emergency"] = relationship(  # noqa: F821
        "Emergency", back_populates="corridors", lazy="noload"
    )

    status: Mapped[CorridorStatus] = mapped_column(
        String(32), nullable=False, default=CorridorStatus.PROPOSED
    )

    # Serialized route as JSON string: list of {node_id, lat, lng}
    route_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_distance_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Approval workflow
    proposed_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Explanation of any conflict resolution
    conflict_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancel_reason: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    corridor_signals: Mapped[list["CorridorSignal"]] = relationship(
        "CorridorSignal", back_populates="corridor",
        lazy="noload", cascade="all, delete-orphan",
        order_by="CorridorSignal.sequence_order"
    )

    __table_args__ = (
        Index("ix_corridors_emergency_status", "emergency_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Corridor id={self.id[:8]} emergency={self.emergency_id[:8]} status={self.status}>"


class CorridorSignal(UUIDMixin, Base):
    """
    One signal in a green corridor schedule.
    Records when the signal should turn green and for how long,
    plus the actual activation time for audit purposes.
    """
    __tablename__ = "corridor_signals"

    corridor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("corridors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    corridor: Mapped["Corridor"] = relationship("Corridor", back_populates="corridor_signals")

    signal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("traffic_signals.id", ondelete="CASCADE"), nullable=False
    )
    signal: Mapped["TrafficSignal"] = relationship("TrafficSignal", back_populates="corridor_signals")

    # Position in the route sequence (0-indexed)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Planned schedule
    planned_green_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    planned_green_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Actual recorded times
    actual_green_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_green_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Was this signal successfully commanded?
    commanded: Mapped[bool] = mapped_column(default=False, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Which conflicting approaches were held RED
    # Stored as comma-separated signal IDs
    conflicting_signal_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_corridor_signals_corridor_seq", "corridor_id", "sequence_order"),
    )

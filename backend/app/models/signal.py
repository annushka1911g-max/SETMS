"""
SETMS — TrafficSignal and SignalEvent models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import SignalMode, SignalPhase, SignalStatus


class TrafficSignal(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "traffic_signals"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    intersection_name: Mapped[str] = mapped_column(String(128), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Current state
    status: Mapped[SignalStatus] = mapped_column(
        String(32), nullable=False, default=SignalStatus.OPERATIONAL
    )
    current_phase: Mapped[SignalPhase] = mapped_column(
        String(32), nullable=False, default=SignalPhase.RED
    )
    current_mode: Mapped[SignalMode] = mapped_column(
        String(32), nullable=False, default=SignalMode.NORMAL
    )

    # Normal cycle timing in seconds
    green_duration_sec: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    yellow_duration_sec: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    red_duration_sec: Mapped[int] = mapped_column(Integer, default=35, nullable=False)

    # Associated road node (intersection)
    road_node_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("road_nodes.id", ondelete="SET NULL"), nullable=True
    )
    road_node: Mapped[Optional["RoadNode"]] = relationship(  # noqa: F821
        "RoadNode", lazy="noload"
    )

    # Associated IoT device
    device_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    device: Mapped[Optional["Device"]] = relationship(  # noqa: F821
        "Device", lazy="noload"
    )

    # Approach directions this signal controls (comma-separated: N,S,E,W)
    approach_directions: Mapped[str] = mapped_column(String(16), default="N,S", nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    events: Mapped[list["SignalEvent"]] = relationship(
        "SignalEvent", back_populates="signal", lazy="noload", cascade="all, delete-orphan"
    )
    corridor_signals: Mapped[list["CorridorSignal"]] = relationship(  # noqa: F821
        "CorridorSignal", back_populates="signal", lazy="noload"
    )

    __table_args__ = (
        Index("ix_signals_status", "status"),
        Index("ix_signals_node", "road_node_id"),
    )

    def __repr__(self) -> str:
        return f"<TrafficSignal {self.name} phase={self.current_phase}>"


class SignalEvent(UUIDMixin, Base):
    """Immutable audit record of every signal state change."""
    __tablename__ = "signal_events"

    signal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("traffic_signals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    signal: Mapped["TrafficSignal"] = relationship("TrafficSignal", back_populates="events")

    from_phase: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    to_phase: Mapped[str] = mapped_column(String(32), nullable=False)
    from_mode: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    to_mode: Mapped[str] = mapped_column(String(32), nullable=False)

    # What triggered this change
    trigger: Mapped[str] = mapped_column(String(64), nullable=False, default="NORMAL_CYCLE")
    triggered_by_emergency_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )
    triggered_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index("ix_signal_events_signal_occurred", "signal_id", "occurred_at"),
    )

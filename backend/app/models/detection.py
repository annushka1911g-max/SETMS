"""
SETMS — VehicleDetection and TrafficDensitySnapshot models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.base import UUIDMixin
from app.models.enums import DataSource, DensityLevel


class VehicleDetection(UUIDMixin, Base):
    """
    A single vehicle detection event from the AI engine.
    Includes bounding box, confidence score, and vehicle class.
    """
    __tablename__ = "vehicle_detections"

    # Source camera / signal / device
    signal_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("traffic_signals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    device_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )

    # Detection details
    vehicle_class: Mapped[str] = mapped_column(String(64), nullable=False)  # car, truck, ambulance, ...
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_ambulance_candidate: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Bounding box in normalized [0,1] coordinates
    bbox_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_w: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Track ID for multi-frame tracking
    track_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    source: Mapped[DataSource] = mapped_column(
        String(32), nullable=False, default=DataSource.AI_ESTIMATED
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Optional: frame reference
    frame_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_vehicle_detections_signal_detected", "signal_id", "detected_at"),
    )


class TrafficDensitySnapshot(UUIDMixin, Base):
    """
    Periodic snapshot of traffic density at a signal/intersection.
    Density values are AI-estimated, manually entered, or simulated.
    """
    __tablename__ = "traffic_density_snapshots"

    signal_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("traffic_signals.id", ondelete="SET NULL"), nullable=True, index=True
    )

    vehicle_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    queue_length_estimate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    occupancy_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0-1.0

    density_level: Mapped[DensityLevel] = mapped_column(
        String(16), nullable=False, default=DensityLevel.LOW
    )

    # IMPORTANT: always label how this data was produced
    data_source: Mapped[DataSource] = mapped_column(
        String(32), nullable=False, default=DataSource.SIMULATED
    )

    region_of_interest: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]

    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index("ix_density_snapshots_signal_captured", "signal_id", "captured_at"),
    )

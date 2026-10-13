"""
SETMS — RoadNode and RoadEdge models (graph for routing).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class RoadNode(UUIDMixin, TimestampMixin, Base):
    """
    A node in the road graph — typically an intersection or waypoint.
    """
    __tablename__ = "road_nodes"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Is this node a controlled intersection?
    is_intersection: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Optionally linked to a hospital
    hospital_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True
    )

    # Outgoing edges from this node
    edges_from: Mapped[list["RoadEdge"]] = relationship(
        "RoadEdge",
        foreign_keys="RoadEdge.from_node_id",
        back_populates="from_node",
        lazy="noload",
    )
    edges_to: Mapped[list["RoadEdge"]] = relationship(
        "RoadEdge",
        foreign_keys="RoadEdge.to_node_id",
        back_populates="to_node",
        lazy="noload",
    )

    __table_args__ = (
        Index("ix_road_nodes_location", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<RoadNode {self.name} ({self.latitude:.4f}, {self.longitude:.4f})>"


class RoadEdge(UUIDMixin, Base):
    """
    A directed edge connecting two road nodes.
    Speed and congestion factor are used for ETA estimation.
    """
    __tablename__ = "road_edges"

    from_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("road_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_node: Mapped["RoadNode"] = relationship(
        "RoadNode", foreign_keys=[from_node_id], back_populates="edges_from"
    )

    to_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("road_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    to_node: Mapped["RoadNode"] = relationship(
        "RoadNode", foreign_keys=[to_node_id], back_populates="edges_to"
    )

    distance_meters: Mapped[float] = mapped_column(Float, nullable=False)
    # Free-flow speed limit
    speed_limit_kmh: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    # Congestion factor: 1.0 = free flow, higher = slower. Simulated or AI-estimated.
    congestion_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    road_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    # Number of lanes in this direction
    lanes: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    is_one_way: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_passable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def travel_time_seconds(self) -> float:
        """Estimated travel time accounting for congestion."""
        effective_speed = self.speed_limit_kmh / max(self.congestion_factor, 0.1)
        return (self.distance_meters / 1000.0) / max(effective_speed, 1.0) * 3600.0

    __table_args__ = (
        Index("ix_road_edges_from_to", "from_node_id", "to_node_id"),
    )

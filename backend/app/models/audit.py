"""
SETMS — AuditLog model for sensitive operations.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import UUIDMixin


class AuditLog(UUIDMixin, Base):
    """
    Immutable record of significant operations performed by users or the system.
    Never delete audit logs.
    """
    __tablename__ = "audit_logs"

    # Who performed the action (null = system)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user: Mapped[Optional["User"]] = relationship(  # noqa: F821
        "User", back_populates="audit_logs", lazy="noload"
    )

    # What was done
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # What type of resource was affected
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    # The affected resource's ID
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)

    # Machine-readable details (JSON)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Human-readable summary
    summary: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Source IP or client identifier
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_occurred", "occurred_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} resource={self.resource_type}/{self.resource_id}>"

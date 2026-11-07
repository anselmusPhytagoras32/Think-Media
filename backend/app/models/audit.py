"""Durable privileged-action audit trail (FR11, NFR02)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.time_utils import utcnow


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=text("now()")
    )

    __table_args__ = (
        CheckConstraint("char_length(action) BETWEEN 1 AND 100", name="action_length"),
        CheckConstraint(
            "old_status IS NULL OR old_status IN ('pending', 'verified', 'rejected')",
            name="old_status_allowed",
        ),
        CheckConstraint(
            "new_status IN ('verified', 'rejected')", name="new_status_allowed"
        ),
        CheckConstraint("char_length(reason) BETWEEN 1 AND 1000", name="reason_length"),
        Index("ix_audit_events_created_at_id", "created_at", "id"),
        Index("ix_audit_events_actor_id", "actor_id"),
        Index("ix_audit_events_target_id", "target_id"),
    )

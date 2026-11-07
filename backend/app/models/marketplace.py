"""FR04–07 private marketplace records and atomic event history."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.time_utils import utcnow


class Listing(Base):
    __tablename__ = "listings"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("company_profiles.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(10000))
    requirements: Mapped[str] = mapped_column(String(10000))
    location: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(10))
    skills: Mapped[list[str]] = mapped_column(ARRAY(Text))
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','published','closed')", name="status_allowed"
        ),
        CheckConstraint("type IN ('ojt','job')", name="type_allowed"),
        CheckConstraint("cardinality(skills) <= 30", name="skills_count"),
    )


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(
        String(40), unique=True, default=lambda: "TM-" + uuid.uuid4().hex.upper()
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("listings.id", ondelete="RESTRICT"), index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="submitted")
    cover_letter: Mapped[str] = mapped_column(String(5000))
    attachment_name: Mapped[str] = mapped_column(String(200))
    attachment: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    __table_args__ = (
        UniqueConstraint(
            "student_id", "listing_id", name="uq_application_student_listing"
        ),
        CheckConstraint(
            "status IN ('submitted','under_review','accepted','rejected')",
            name="status_allowed",
        ),
        CheckConstraint(
            "octet_length(attachment) BETWEEN 1 AND 5242880", name="attachment_size"
        ),
    )


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="RESTRICT"), index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    __table_args__ = (
        CheckConstraint(
            "new_status IN ('submitted','under_review','accepted','rejected')",
            name="new_status_allowed",
        ),
        CheckConstraint(
            "old_status IS NULL OR old_status IN ('submitted','under_review','accepted','rejected')",
            name="old_status_allowed",
        ),
    )


class MarketplaceEvent(Base):
    __tablename__ = "marketplace_events"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("listings.id", ondelete="RESTRICT"), index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    action: Mapped[str] = mapped_column(String(20))
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

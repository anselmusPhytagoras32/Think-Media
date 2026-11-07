"""Role-specific profile models.

Instructors deliberately live in ``instructor_profiles``; they are never
represented as students. Profile tables are separate so a company profile can
carry verification state without leaking it into other roles.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.time_utils import utcnow


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    institution: Mapped[str] = mapped_column(
        String(200), nullable=False, default="", server_default=text("''")
    )
    program: Mapped[str] = mapped_column(
        String(200), nullable=False, default="", server_default=text("''")
    )
    location: Mapped[str] = mapped_column(
        String(200), nullable=False, default="", server_default=text("''")
    )
    background: Mapped[str] = mapped_column(
        String(2000), nullable=False, default="", server_default=text("''")
    )
    skills: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default=text("'{}'::text[]")
    )
    interests: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default=text("'{}'::text[]")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=text("now()"),
    )

    __table_args__ = (
        CheckConstraint("char_length(institution) <= 200", name="institution_length"),
        CheckConstraint("char_length(program) <= 200", name="program_length"),
        CheckConstraint("char_length(location) <= 200", name="location_length"),
        CheckConstraint("char_length(background) <= 2000", name="background_length"),
        CheckConstraint("cardinality(skills) <= 30", name="skills_count"),
        CheckConstraint("cardinality(interests) <= 30", name="interests_count"),
    )


class InstructorProfile(Base):
    __tablename__ = "instructor_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    institution: Mapped[str] = mapped_column(
        String(200), nullable=False, default="", server_default=text("''")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=text("now()"),
    )

    __table_args__ = (
        CheckConstraint("char_length(institution) <= 200", name="institution_length"),
    )


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(
        String(2000), nullable=False, default="", server_default=text("''")
    )
    location: Mapped[str] = mapped_column(
        String(200), nullable=False, default="", server_default=text("''")
    )
    contact_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    website: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
    verification_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=text("now()"),
    )

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_company_profiles_user_id"),
        CheckConstraint(
            "verification_status IN ('pending', 'verified', 'rejected')",
            name="verification_status_allowed",
        ),
        CheckConstraint("verification_version >= 1", name="verification_version_positive"),
        CheckConstraint("char_length(company_name) BETWEEN 1 AND 200", name="company_name_length"),
        CheckConstraint("char_length(description) <= 2000", name="description_length"),
        CheckConstraint("char_length(location) <= 200", name="location_length"),
        CheckConstraint(
            "website IS NULL OR char_length(website) <= 2048", name="website_length"
        ),
        Index(
            "ix_company_profiles_status_created_at",
            "verification_status",
            "created_at",
        ),
    )

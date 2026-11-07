"""User account model (FR01, NFR02)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.time_utils import utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
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
        CheckConstraint(
            "role IN ('student', 'instructor', 'company', 'administrator')",
            name="role_allowed",
        ),
        CheckConstraint(
            "char_length(email) BETWEEN 3 AND 254", name="email_length"
        ),
        CheckConstraint("email = lower(email)", name="email_normalized"),
        CheckConstraint(
            "char_length(display_name) BETWEEN 1 AND 100", name="display_name_length"
        ),
    )

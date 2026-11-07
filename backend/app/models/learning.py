"""FR03/10/11 learning, attempts and moderation with private answer keys."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.time_utils import utcnow


class LearningContent(Base):
    __tablename__ = "learning_content"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(String(20000))
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text))
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','published','archived')", name="status_allowed"
        ),
        CheckConstraint("cardinality(tags)<=30", name="tags_count"),
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_content.id", ondelete="RESTRICT"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(String(1000))
    options: Mapped[list[str]] = mapped_column(ARRAY(Text))
    correct_index: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        CheckConstraint("cardinality(options) BETWEEN 2 AND 6", name="options_count"),
        CheckConstraint(
            "correct_index >= 0 AND correct_index < cardinality(options)",
            name="correct_index_valid",
        ),
        UniqueConstraint("content_id", "position"),
    )


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_content.id", ondelete="RESTRICT"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    answers: Mapped[dict] = mapped_column(JSONB)
    correct: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    __table_args__ = (
        CheckConstraint(
            "total>0 AND correct>=0 AND correct<=total", name="score_valid"
        ),
    )


class ContentState(Base):
    __tablename__ = "content_states"
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_content.id", ondelete="RESTRICT"), primary_key=True
    )
    saved: Mapped[bool] = mapped_column(Boolean, default=False)
    reacted: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class ModerationReport(Base):
    __tablename__ = "moderation_reports"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_content.id", ondelete="RESTRICT"), index=True
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    reason: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    resolution: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    __table_args__ = (
        CheckConstraint("status IN ('pending','resolved')", name="status_allowed"),
        CheckConstraint(
            "(status='pending' AND resolved_by IS NULL AND resolved_at IS NULL AND resolution IS NULL) OR (status='resolved' AND resolved_by IS NOT NULL AND resolved_at IS NOT NULL AND resolution IS NOT NULL)",
            name="resolution_consistent",
        ),
    )


class ContentEvent(Base):
    __tablename__ = "content_events"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_content.id", ondelete="RESTRICT"), index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    action: Mapped[str] = mapped_column(String(40))
    detail: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

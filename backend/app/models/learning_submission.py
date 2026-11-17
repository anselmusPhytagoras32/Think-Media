"""FR03/11 instructor-owned submissions and administrator review history."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, LargeBinary, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.time_utils import utcnow


class LearningSubmission(Base):
    __tablename__ = "learning_submissions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    kind: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict] = mapped_column(JSONB)
    attachment_name: Mapped[str | None] = mapped_column(String(200))
    attachment: Mapped[bytes | None] = mapped_column(LargeBinary, deferred=True)
    published_content_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("learning_content.id", ondelete="RESTRICT"), unique=True
    )
    approved_skill_key: Mapped[str | None] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    __table_args__ = (
        CheckConstraint("kind IN ('lesson', 'skill')", name="kind_allowed"),
        CheckConstraint("status IN ('draft', 'pending', 'changes_requested', 'approved')", name="status_allowed"),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint("(attachment IS NULL) = (attachment_name IS NULL)", name="attachment_pair"),
        CheckConstraint("kind = 'lesson' OR attachment IS NULL", name="lesson_attachment"),
        CheckConstraint(
            "(published_content_id IS NOT NULL) = (kind = 'lesson' AND status = 'approved')",
            name="published_content",
        ),
        CheckConstraint(
            "(approved_skill_key IS NOT NULL) = (kind = 'skill' AND status = 'approved')",
            name="approved_skill",
        ),
        Index("ix_learning_submissions_author_updated", "author_id", "updated_at", "id"),
        Index("ix_learning_submissions_status_updated", "status", "updated_at", "id"),
    )


class LearningReview(Base):
    __tablename__ = "learning_reviews"

    submission_id: Mapped[UUID] = mapped_column(
        ForeignKey("learning_submissions.id", ondelete="CASCADE"), primary_key=True
    )
    submitted_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    decision: Mapped[str] = mapped_column(String(20))
    feedback: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        CheckConstraint("decision IN ('approved', 'changes_requested')", name="decision_allowed"),
    )

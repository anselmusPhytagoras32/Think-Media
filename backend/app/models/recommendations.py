"""FR09 actual interactions; typed foreign keys prevent orphan item references."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.time_utils import utcnow


class Interaction(Base):
    __tablename__ = "interactions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    listing_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("listings.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    content_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("learning_content.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(10))
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    __table_args__ = (
        CheckConstraint(
            "(listing_id IS NOT NULL AND content_id IS NULL) OR (listing_id IS NULL AND content_id IS NOT NULL)",
            name="one_item",
        ),
        CheckConstraint(
            "(event_type='view' AND rating IS NULL) OR (event_type='rating' AND rating BETWEEN 1 AND 5 AND rating IS NOT NULL)",
            name="event_rating_valid",
        ),
        Index(
            "uq_interactions_listing_rating",
            "user_id",
            "listing_id",
            unique=True,
            postgresql_where=text("event_type='rating'"),
        ),
        Index(
            "uq_interactions_content_rating",
            "user_id",
            "content_id",
            unique=True,
            postgresql_where=text("event_type='rating'"),
        ),
    )

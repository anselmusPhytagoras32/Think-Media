"""Audit event repository. Writes only; there is no update/delete API."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditEvent


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        actor_id: uuid.UUID,
        action: str,
        target_id: uuid.UUID,
        old_status: str | None,
        new_status: str,
        reason: str,
    ) -> AuditEvent:
        event = AuditEvent(
            actor_id=actor_id,
            action=action,
            target_id=target_id,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def list(self, *, limit: int, offset: int) -> list[AuditEvent]:
        statement = (
            select(AuditEvent)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(statement).all())

    def count(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(AuditEvent)) or 0)

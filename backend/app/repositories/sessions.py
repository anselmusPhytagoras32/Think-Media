"""Session repository. Only token hashes are stored."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SessionToken


class SessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_token_hash(self, token_hash: str) -> SessionToken | None:
        return self.db.scalar(
            select(SessionToken).where(SessionToken.token_hash == token_hash)
        )

    def get_by_id(self, session_id: uuid.UUID) -> SessionToken | None:
        return self.db.get(SessionToken, session_id)

    def create(
        self,
        *,
        token_hash: str,
        expires_at: datetime,
        user_id: uuid.UUID | None,
        created_at: datetime | None = None,
    ) -> SessionToken:
        row = SessionToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            **({"created_at": created_at} if created_at is not None else {}),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def revoke(self, row: SessionToken, now: datetime) -> None:
        if row.revoked_at is None:
            row.revoked_at = now
            self.db.flush()

    def delete_for_user(self, user_id: uuid.UUID) -> int:
        rows = self.db.scalars(
            select(SessionToken).where(SessionToken.user_id == user_id)
        ).all()
        for row in rows:
            self.db.delete(row)
        self.db.flush()
        return len(rows)

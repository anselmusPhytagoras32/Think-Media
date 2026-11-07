"""User repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, normalized_email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == normalized_email))

    def create(
        self,
        *,
        email: str,
        password_hash: str,
        display_name: str,
        role: str,
        user_id: uuid.UUID | None = None,
    ) -> User:
        user = User(
            id=user_id or uuid.uuid4(),
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update_display_name(self, user: User, display_name: str) -> User:
        user.display_name = display_name
        self.db.flush()
        return user

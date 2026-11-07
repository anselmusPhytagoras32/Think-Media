"""Profile repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CompanyProfile, InstructorProfile, StudentProfile


class ProfileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- reads -------------------------------------------------------------

    def get_student(self, user_id: uuid.UUID) -> StudentProfile | None:
        return self.db.get(StudentProfile, user_id)

    def get_instructor(self, user_id: uuid.UUID) -> InstructorProfile | None:
        return self.db.get(InstructorProfile, user_id)

    def get_company_by_user_id(self, user_id: uuid.UUID) -> CompanyProfile | None:
        return self.db.scalar(
            select(CompanyProfile).where(CompanyProfile.user_id == user_id)
        )

    def get_company_by_id(
        self, company_id: uuid.UUID, *, for_update: bool = False
    ) -> CompanyProfile | None:
        statement = select(CompanyProfile).where(CompanyProfile.id == company_id)
        if for_update:
            statement = statement.with_for_update()
        return self.db.execute(statement).scalar_one_or_none()

    def list_companies(
        self, *, status: str | None, limit: int, offset: int
    ) -> list[CompanyProfile]:
        statement = select(CompanyProfile)
        if status is not None:
            statement = statement.where(CompanyProfile.verification_status == status)
        statement = statement.order_by(
            CompanyProfile.created_at.asc(), CompanyProfile.id.asc()
        ).limit(limit).offset(offset)
        return list(self.db.scalars(statement).all())

    def count_companies(self, *, status: str | None) -> int:
        statement = select(func.count()).select_from(CompanyProfile)
        if status is not None:
            statement = statement.where(CompanyProfile.verification_status == status)
        return int(self.db.scalar(statement) or 0)

    # -- writes ------------------------------------------------------------

    def create_student(self, user_id: uuid.UUID) -> StudentProfile:
        row = StudentProfile(
            user_id=user_id, institution="", program="", skills=[], interests=[]
        )
        self.db.add(row)
        self.db.flush()
        return row

    def create_instructor(self, user_id: uuid.UUID) -> InstructorProfile:
        row = InstructorProfile(user_id=user_id, institution="")
        self.db.add(row)
        self.db.flush()
        return row

    def create_company(
        self, *, user_id: uuid.UUID, company_name: str
    ) -> CompanyProfile:
        row = CompanyProfile(
            user_id=user_id,
            company_name=company_name,
            description="",
            location="",
            website=None,
            verification_status="pending",
            verification_version=1,
        )
        self.db.add(row)
        self.db.flush()
        return row

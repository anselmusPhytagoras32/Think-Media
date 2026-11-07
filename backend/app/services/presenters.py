"""Convert domain rows into contracted response envelopes."""

from __future__ import annotations

from app.enums import Role
from app.errors import ApiError
from app.models import CompanyProfile, User
from app.repositories import ProfileRepository
from app.schemas import (
    AdministratorProfileOut,
    AuditEventOut,
    CompanyProfileOut,
    CompanyReviewOut,
    InstructorProfileOut,
    ProfileEnvelope,
    ProfileOut,
    StudentProfileOut,
    UserOut,
)


def user_out(user: User) -> UserOut:
    return UserOut.model_validate(user)


def profile_out(repo: ProfileRepository, user: User) -> ProfileOut:
    if user.role == Role.STUDENT:
        row = repo.get_student(user.id)
        if row is None:
            raise ApiError(500, "INTERNAL_ERROR", "Student profile is missing.")
        return StudentProfileOut.model_validate(row)
    if user.role == Role.INSTRUCTOR:
        row = repo.get_instructor(user.id)
        if row is None:
            raise ApiError(500, "INTERNAL_ERROR", "Instructor profile is missing.")
        return InstructorProfileOut.model_validate(row)
    if user.role == Role.COMPANY:
        row = repo.get_company_by_user_id(user.id)
        if row is None:
            raise ApiError(500, "INTERNAL_ERROR", "Company profile is missing.")
        return CompanyProfileOut.model_validate(row)
    if user.role == Role.ADMINISTRATOR:
        return AdministratorProfileOut()
    raise ApiError(500, "INTERNAL_ERROR", "Unknown account role.")


def envelope(repo: ProfileRepository, user: User) -> ProfileEnvelope:
    return ProfileEnvelope(user=user_out(user), profile=profile_out(repo, user))


def company_review(row: CompanyProfile) -> CompanyReviewOut:
    return CompanyReviewOut.model_validate(row)


def audit_event_out(event) -> AuditEventOut:
    return AuditEventOut.model_validate(event)

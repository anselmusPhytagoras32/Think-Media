"""Domain enums shared by models, schemas and services."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    COMPANY = "company"
    ADMINISTRATOR = "administrator"

    @classmethod
    def public(cls) -> frozenset[str]:
        return frozenset({cls.STUDENT, cls.INSTRUCTOR, cls.COMPANY})


class VerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class AuditAction(StrEnum):
    COMPANY_VERIFICATION_CHANGED = "company.verification_changed"

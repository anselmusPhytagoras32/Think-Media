"""Pydantic API schemas (strict: unknown fields are rejected)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.enums import Role, VerificationStatus
from app.time_utils import iso_manila
from app.validation import (
    normalize_display_name,
    normalize_email,
    normalize_profile_text,
    normalize_string_list,
    normalize_website,
    validate_password,
)


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OrmModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class UserOut(OrmModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: Role
    created_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime) -> str:
        return iso_manila(value)


class StudentProfileOut(OrmModel):
    kind: Literal["student"] = "student"
    institution: str
    program: str
    location: str
    background: str
    skills: list[str]
    interests: list[str]


class InstructorProfileOut(OrmModel):
    kind: Literal["instructor"] = "instructor"
    institution: str


class CompanyProfileOut(OrmModel):
    kind: Literal["company"] = "company"
    company_name: str
    description: str
    location: str
    website: str | None
    contact_email: str | None
    contact_phone: str | None
    verification_status: VerificationStatus
    verification_version: int


class AdministratorProfileOut(OrmModel):
    kind: Literal["administrator"] = "administrator"


ProfileOut = Annotated[
    StudentProfileOut | InstructorProfileOut | CompanyProfileOut | AdministratorProfileOut,
    Field(discriminator="kind"),
]


class ProfileEnvelope(ApiModel):
    user: UserOut
    profile: ProfileOut


class CsrfResponse(ApiModel):
    csrf_token: str


class CompanyReviewOut(OrmModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    description: str
    location: str
    website: str | None
    contact_email: str | None
    contact_phone: str | None
    verification_status: VerificationStatus
    verification_version: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _serialize_timestamps(self, value: datetime) -> str:
        return iso_manila(value)


class AuditEventOut(OrmModel):
    id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    target_id: uuid.UUID
    old_status: VerificationStatus | None
    new_status: VerificationStatus
    reason: str
    created_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime) -> str:
        return iso_manila(value)


class CompanyListResponse(ApiModel):
    items: list[CompanyReviewOut]
    total: int
    limit: int
    offset: int


class AuditEventListResponse(ApiModel):
    items: list[AuditEventOut]
    total: int
    limit: int
    offset: int


class VerificationUpdateResponse(ApiModel):
    company: CompanyReviewOut
    audit_event: AuditEventOut


class HealthResponse(ApiModel):
    status: Literal["ok"] = "ok"


class ErrorDetail(ApiModel):
    code: str
    message: str
    fields: dict[str, list[str]]
    request_id: str


class ErrorEnvelope(ApiModel):
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


PublicRole = Literal["student", "instructor", "company"]


class RegisterRequest(ApiModel):
    email: str
    password: str
    display_name: str
    role: PublicRole
    company_name: str | None = None

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        return validate_password(value)

    @field_validator("display_name")
    @classmethod
    def _validate_display_name(cls, value: str) -> str:
        return normalize_display_name(value)

    @field_validator("company_name")
    @classmethod
    def _validate_company_name(cls, value: str | None) -> str | None:
        return normalize_profile_text(
            value, field="Company name", max_length=200, allow_empty=False
        )


class LoginRequest(ApiModel):
    email: str
    password: str = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        return normalize_email(value)


class ProfileUpdateRequest(ApiModel):
    """Role-specific editable fields are accepted directly.

    Unknown fields (email, role, id, user_id, verification_status,
    verification_version, is_admin, ...) are rejected by ``extra='forbid'``.
    Fields that do not belong to the authenticated role are rejected by the
    profile service.
    """

    display_name: str | None = None
    institution: str | None = None
    program: str | None = None
    skills: list[str] | None = None
    interests: list[str] | None = None
    company_name: str | None = None
    description: str | None = None
    location: str | None = None
    website: str | None = None
    background: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None

    @field_validator("display_name")
    @classmethod
    def _validate_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_display_name(value)

    @field_validator("institution")
    @classmethod
    def _validate_institution(cls, value: str | None) -> str | None:
        return normalize_profile_text(value, field="Institution", max_length=200)

    @field_validator("program")
    @classmethod
    def _validate_program(cls, value: str | None) -> str | None:
        return normalize_profile_text(value, field="Program", max_length=200)

    @field_validator("company_name")
    @classmethod
    def _validate_company_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_profile_text(
            value, field="Company name", max_length=200, allow_empty=False
        )

    @field_validator("description")
    @classmethod
    def _validate_description(cls, value: str | None) -> str | None:
        return normalize_profile_text(value, field="Description", max_length=2000)

    @field_validator("location")
    @classmethod
    def _validate_location(cls, value: str | None) -> str | None:
        return normalize_profile_text(value, field="Location", max_length=200)

    @field_validator("website")
    @classmethod
    def _validate_website(cls, value: str | None) -> str | None:
        return normalize_website(value)

    @field_validator("background")
    @classmethod
    def _validate_background(cls, value: str | None) -> str | None:
        return normalize_profile_text(value, field="Background", max_length=2000)

    @field_validator("contact_email")
    @classmethod
    def _validate_contact_email(cls, value: str | None) -> str | None:
        return normalize_email(value) if value and value.strip() else None

    @field_validator("contact_phone")
    @classmethod
    def _validate_contact_phone(cls, value: str | None) -> str | None:
        import re

        if value is None or not value.strip():
            return None
        value = value.strip()
        digits = re.sub(r"[^0-9]", "", value)
        if len(value) > 40 or not re.fullmatch(r"\+?[0-9 ()-]+", value) or not 7 <= len(digits) <= 15:
            raise ValueError("Enter a phone number with 7–15 digits and optional +, spaces, parentheses or hyphens.")
        return value

    @field_validator("skills")
    @classmethod
    def _validate_skills(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return normalize_string_list(value, field="Skills")

    @field_validator("interests")
    @classmethod
    def _validate_interests(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return normalize_string_list(value, field="Interests")


class VerificationUpdateRequest(ApiModel):
    status: Literal["verified", "rejected"]
    reason: str
    expected_version: int = Field(ge=1)

    @field_validator("reason")
    @classmethod
    def _validate_reason(cls, value: str) -> str:
        from app.validation import normalize_reason

        return normalize_reason(value)

"""Self-service profile reads and updates (FR02)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.enums import Role
from app.errors import ApiError
from app.models import User
from app.repositories import ProfileRepository, UserRepository
from app.schemas import ProfileEnvelope, ProfileUpdateRequest
from app.services.presenters import envelope

_STUDENT_FIELDS = {"institution", "program", "skills", "interests", "location", "background"}
_INSTRUCTOR_FIELDS = {"institution"}
_COMPANY_FIELDS = {"company_name", "description", "location", "website", "contact_email", "contact_phone"}
_ADMIN_FIELDS: set[str] = set()

_EDITABLE_BY_ROLE = {
    Role.STUDENT: _STUDENT_FIELDS,
    Role.INSTRUCTOR: _INSTRUCTOR_FIELDS,
    Role.COMPANY: _COMPANY_FIELDS,
    Role.ADMINISTRATOR: _ADMIN_FIELDS,
}


class ProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.profiles = ProfileRepository(db)

    def get_me(self, user: User) -> ProfileEnvelope:
        return envelope(self.profiles, user)

    def update_me(self, user: User, payload: ProfileUpdateRequest) -> ProfileEnvelope:
        provided = set(payload.model_fields_set)
        if not provided:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "Request validation failed.",
                fields={"body": ["At least one editable field is required."]},
            )

        allowed = _EDITABLE_BY_ROLE.get(Role(user.role), set())
        forbidden = provided - allowed - {"display_name"}
        if forbidden:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "Request validation failed.",
                fields={
                    field: [f"{field} cannot be edited for a {user.role} account."]
                    for field in sorted(forbidden)
                },
            )

        # Null is not an accepted value for a field that was explicitly sent,
        # except for the nullable company website.
        null_fields = {
            field
            for field in provided
            if field not in {"website", "contact_email", "contact_phone"} and getattr(payload, field) is None
        }
        if null_fields:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "Request validation failed.",
                fields={field: [f"{field} cannot be null."] for field in sorted(null_fields)},
            )

        # Validate the target profile exists before mutating anything.
        profile_row = None
        if user.role == Role.STUDENT:
            profile_row = self.profiles.get_student(user.id)
        elif user.role == Role.INSTRUCTOR:
            profile_row = self.profiles.get_instructor(user.id)
        elif user.role == Role.COMPANY:
            profile_row = self.profiles.get_company_by_user_id(user.id)
        if user.role != Role.ADMINISTRATOR and profile_row is None:
            raise ApiError(500, "INTERNAL_ERROR", "Profile is missing for this account.")

        try:
            if "display_name" in provided:
                self.users.update_display_name(user, payload.display_name or "")
            if profile_row is not None:
                for field in provided:
                    if field == "display_name":
                        continue
                    setattr(profile_row, field, getattr(payload, field))
                self.db.flush()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return envelope(self.profiles, user)

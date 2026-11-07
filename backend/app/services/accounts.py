"""Account registration, login and administrator provisioning (FR01)."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.enums import Role
from app.errors import ApiError
from app.models import User
from app.repositories import ProfileRepository, UserRepository
from app.schemas import LoginRequest, ProfileEnvelope, RegisterRequest
from app.security.passwords import (
    hash_password,
    verify_dummy_password,
    verify_password,
)
from app.services.presenters import envelope
from app.validation import normalize_display_name, normalize_email, validate_password


class AccountService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.profiles = ProfileRepository(db)

    # -- registration ------------------------------------------------------

    def register(self, payload: RegisterRequest) -> ProfileEnvelope:
        role = payload.role
        if role == Role.ADMINISTRATOR:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "Request validation failed.",
                fields={
                    "role": [
                        "Administrator accounts cannot be created through public registration."
                    ]
                },
            )

        company_name = payload.company_name
        if role == Role.COMPANY:
            if not company_name:
                raise ApiError(
                    422,
                    "VALIDATION_ERROR",
                    "Request validation failed.",
                    fields={"company_name": ["Company name is required for company registration."]},
                )
        elif company_name:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "Request validation failed.",
                fields={
                    "company_name": [
                        "Company name is only accepted for company registration."
                    ]
                },
            )

        try:
            user = self.users.create(
                email=payload.email,
                password_hash=hash_password(payload.password),
                display_name=payload.display_name,
                role=role,
            )
            if role == Role.STUDENT:
                self.profiles.create_student(user.id)
            elif role == Role.INSTRUCTOR:
                self.profiles.create_instructor(user.id)
            elif role == Role.COMPANY:
                self.profiles.create_company(
                    user_id=user.id, company_name=company_name or ""
                )
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            if self.users.get_by_email(payload.email) is not None:
                raise ApiError(
                    409, "EMAIL_EXISTS", "An account with that email already exists."
                ) from None
            raise

        return envelope(self.profiles, user)

    # -- login -------------------------------------------------------------

    def authenticate(self, email: str, password: str) -> User:
        try:
            normalized = normalize_email(email)
        except ValueError:
            verify_dummy_password(password)
            raise ApiError(401, "INVALID_CREDENTIALS", "Invalid email or password.") from None

        user = self.users.get_by_email(normalized)
        if user is None:
            verify_dummy_password(password)
            raise ApiError(401, "INVALID_CREDENTIALS", "Invalid email or password.")
        if not verify_password(password, user.password_hash):
            raise ApiError(401, "INVALID_CREDENTIALS", "Invalid email or password.")
        return user

    def login(self, payload: LoginRequest) -> ProfileEnvelope:
        user = self.authenticate(payload.email, payload.password)
        return envelope(self.profiles, user)

    # -- administrator provisioning (CLI only) -----------------------------

    def create_administrator(
        self, *, email: str, password: str, display_name: str
    ) -> User:
        """Provision an administrator. Never exposed through an HTTP endpoint."""

        normalized_email = normalize_email(email)
        normalized_name = normalize_display_name(display_name)
        validate_password(password)

        if self.users.get_by_email(normalized_email) is not None:
            raise ApiError(
                409, "EMAIL_EXISTS", "An account with that email already exists."
            )

        try:
            user = self.users.create(
                email=normalized_email,
                password_hash=hash_password(password),
                display_name=normalized_name,
                role=Role.ADMINISTRATOR,
            )
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ApiError(
                409, "EMAIL_EXISTS", "An account with that email already exists."
            ) from None
        return user

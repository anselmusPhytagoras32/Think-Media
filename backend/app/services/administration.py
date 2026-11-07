"""Company verification administration (FR11, NFR04)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.enums import AuditAction, Role, VerificationStatus
from app.errors import ApiError
from app.models import AuditEvent, User
from app.repositories import AuditRepository, ProfileRepository
from app.schemas import (
    AuditEventListResponse,
    CompanyListResponse,
    CompanyReviewOut,
    VerificationUpdateResponse,
)
from app.services.presenters import audit_event_out, company_review
from app.time_utils import utcnow


class AdministrationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.profiles = ProfileRepository(db)
        self.audit = AuditRepository(db)

    # -- company review queue ---------------------------------------------

    def list_companies(
        self, *, status: str | None, limit: int, offset: int
    ) -> CompanyListResponse:
        rows = self.profiles.list_companies(status=status, limit=limit, offset=offset)
        total = self.profiles.count_companies(status=status)
        return CompanyListResponse(
            items=[company_review(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_company(self, company_id: uuid.UUID) -> CompanyReviewOut:
        row = self.profiles.get_company_by_id(company_id)
        if row is None:
            raise ApiError(404, "NOT_FOUND", "Company not found.")
        return company_review(row)

    # -- verification ------------------------------------------------------

    def change_verification(
        self,
        *,
        company_id: uuid.UUID,
        new_status: str,
        reason: str,
        expected_version: int,
        actor: User,
    ) -> VerificationUpdateResponse:
        # Defence in depth: the HTTP dependency already re-loads the current
        # role, but a direct service caller must not bypass the role check.
        if actor.role != Role.ADMINISTRATOR:
            raise ApiError(
                403, "FORBIDDEN", "Administrator privileges are required."
            )
        if new_status not in {VerificationStatus.VERIFIED, VerificationStatus.REJECTED}:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "Request validation failed.",
                fields={"status": ["Status must be 'verified' or 'rejected'."]},
            )

        try:
            row = self.profiles.get_company_by_id(company_id, for_update=True)
            if row is None:
                raise ApiError(404, "NOT_FOUND", "Company not found.")

            # Decisions use the locked, current server state. The client's
            # expected_version only detects a stale screen; it can never
            # override the stored status or version.
            if (
                row.verification_version != expected_version
                or row.verification_status != VerificationStatus.PENDING
            ):
                raise ApiError(
                    409,
                    "VERIFICATION_CONFLICT",
                    "The company verification state changed. Refresh and try again.",
                )

            old_status = row.verification_status
            row.verification_status = new_status
            row.verification_version = row.verification_version + 1
            row.updated_at = utcnow()
            self.db.flush()

            event: AuditEvent = self.audit.create(
                actor_id=actor.id,
                action=AuditAction.COMPANY_VERIFICATION_CHANGED.value,
                target_id=row.id,
                old_status=old_status,
                new_status=new_status,
                reason=reason,
            )
            self.db.flush()

            # Status/version and the audit row commit together or not at all.
            self.db.commit()
        except ApiError:
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise

        # Reload in a clean state so the response reflects committed rows.
        self.db.refresh(row)
        self.db.refresh(event)
        return VerificationUpdateResponse(
            company=company_review(row), audit_event=audit_event_out(event)
        )

    # -- audit -------------------------------------------------------------

    def list_audit_events(self, *, limit: int, offset: int) -> AuditEventListResponse:
        rows = self.audit.list(limit=limit, offset=offset)
        total = self.audit.count()
        return AuditEventListResponse(
            items=[audit_event_out(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

"""Reusable verified-company authorization foundation (FR06/FR11 groundwork).

Phase 1 does not add listings. This service/dependency exists so Phase 2 can
guard every write with the company's *current* database verification state.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.enums import Role, VerificationStatus
from app.errors import ApiError
from app.models import CompanyProfile, User
from app.repositories import ProfileRepository


@dataclass(frozen=True)
class VerifiedCompany:
    user: User
    company: CompanyProfile


def ensure_verified_company(
    user: User, company: CompanyProfile | None
) -> VerifiedCompany:
    """Raise 403 COMPANY_NOT_VERIFIED unless the stored status is verified.

    Callers must pass a freshly loaded company row; no status is read from the
    client or from a cached session payload.
    """

    if (
        user.role != Role.COMPANY
        or company is None
        or company.verification_status != VerificationStatus.VERIFIED
    ):
        raise ApiError(
            403,
            "COMPANY_NOT_VERIFIED",
            "Only verified company accounts may perform this action.",
        )
    return VerifiedCompany(user=user, company=company)


def load_verified_company(db: Session, user: User) -> VerifiedCompany:
    company = ProfileRepository(db).get_company_by_user_id(user.id)
    return ensure_verified_company(user, company)

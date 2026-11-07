"""Administrator verification and audit routes (FR11)."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_administrator, require_csrf
from app.api.responses import ADMIN_ERRORS
from app.models import SessionToken, User
from app.schemas import (
    AuditEventListResponse,
    CompanyListResponse,
    CompanyReviewOut,
    VerificationUpdateRequest,
    VerificationUpdateResponse,
)
from app.services.administration import AdministrationService

router = APIRouter(prefix="/admin", tags=["administration"], responses=ADMIN_ERRORS)


@router.get("/companies", response_model=CompanyListResponse)
def list_companies(
    status: Literal["pending", "verified", "rejected"] | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> CompanyListResponse:
    effective_status = status if status is not None else "pending"
    return AdministrationService(db).list_companies(
        status=effective_status, limit=limit, offset=offset
    )


@router.get("/companies/{company_id}", response_model=CompanyReviewOut)
def get_company(
    company_id: uuid.UUID,
    _admin: User = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> CompanyReviewOut:
    return AdministrationService(db).get_company(company_id)


@router.patch(
    "/companies/{company_id}/verification",
    response_model=VerificationUpdateResponse,
)
def update_company_verification(
    company_id: uuid.UUID,
    payload: VerificationUpdateRequest,
    admin: User = Depends(require_administrator),
    _csrf: SessionToken = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> VerificationUpdateResponse:
    return AdministrationService(db).change_verification(
        company_id=company_id,
        new_status=payload.status,
        reason=payload.reason,
        expected_version=payload.expected_version,
        actor=admin,
    )


@router.get("/audit-events", response_model=AuditEventListResponse)
def list_audit_events(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> AuditEventListResponse:
    return AdministrationService(db).list_audit_events(limit=limit, offset=offset)

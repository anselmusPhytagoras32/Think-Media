"""FR04–07 HTTP marketplace adapters; session/CSRF protected."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_csrf
from app.models import User
from app.schemas.marketplace import ListingInput, ListingPatch, StatusInput
from app.services.marketplace import MarketplaceService

router = APIRouter(tags=["marketplace"])
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


def service(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return MarketplaceService(db, user)


@router.get("/listings")
def listings(
    q: Annotated[str | None, Query(max_length=200)] = None,
    location: Annotated[str | None, Query(max_length=200)] = None,
    type: Literal["ojt", "job"] | None = None,
    skill: Annotated[str | None, Query(max_length=80)] = None,
    limit: Limit = 20,
    offset: Offset = 0,
    s=Depends(service),
):
    return s.list_listings(
        limit, offset, q=q, location=location, type=type, skill=skill
    )


@router.get("/listings/{id}")
def listing(id: UUID, s=Depends(service)):
    return s.listing_detail(id)


@router.get("/company/listings")
def own_listings(limit: Limit = 20, offset: Offset = 0, s=Depends(service)):
    return s.list_listings(limit, offset, own=True)


@router.post("/company/listings", status_code=201, dependencies=[Depends(require_csrf)])
def create(payload: ListingInput, s=Depends(service)):
    return s.create_listing(payload)


@router.patch("/company/listings/{id}", dependencies=[Depends(require_csrf)])
def edit(id: UUID, payload: ListingPatch, s=Depends(service)):
    return s.edit_listing(id, payload)


@router.post("/company/listings/{id}/publish", dependencies=[Depends(require_csrf)])
def publish(id: UUID, s=Depends(service)):
    return s.transition_listing(id, "published")


@router.post("/company/listings/{id}/close", dependencies=[Depends(require_csrf)])
def close(id: UUID, s=Depends(service)):
    return s.transition_listing(id, "closed")


@router.post(
    "/listings/{id}/applications", status_code=201, dependencies=[Depends(require_csrf)]
)
def submit(
    id: UUID,
    file: Annotated[UploadFile, File()],
    cover_letter: Annotated[str, Form(max_length=5000)] = "",
    s=Depends(service),
):
    try:
        data = file.file.read(5 * 1024 * 1024 + 1)
        return s.submit(id, cover_letter, file.filename, file.content_type, data)
    finally:
        file.file.close()


@router.get("/applications/me")
def my_applications(limit: Limit = 20, offset: Offset = 0, s=Depends(service)):
    return s.list_applications(limit, offset)


@router.get("/company/applications")
def company_applications(
    listing_id: UUID | None = None,
    limit: Limit = 20,
    offset: Offset = 0,
    s=Depends(service),
):
    return s.list_applications(limit, offset, company=True, listing_id=listing_id)


@router.get("/applications/{id}")
def application(id: UUID, s=Depends(service)):
    return s.application_out(s.authorized_application(id))


@router.get("/applications/{id}/attachment")
def attachment(id: UUID, s=Depends(service)):
    row = s.authorized_application(id)
    return Response(
        row.attachment,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{row.attachment_name}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.patch("/applications/{id}/status", dependencies=[Depends(require_csrf)])
def status(id: UUID, payload: StatusInput, s=Depends(service)):
    return s.change_status(id, payload.status)

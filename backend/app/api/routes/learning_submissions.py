"""FR03/11 instructor authoring, private previews and skill discovery."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from pydantic import ValidationError

from app.api.deps import get_current_user, get_db, require_csrf
from app.errors import ApiError
from app.schemas.learning_submission import ReviewDecision, SubmissionVersion, draft_adapter
from app.services.learning_submissions import SubmissionService
from app.uploads import MAX_PDF_BYTES, pdf_filename

router = APIRouter(tags=["learning"])
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


def service(db=Depends(get_db), user=Depends(get_current_user)):
    return SubmissionService(db, user)


async def form(
    draft: Annotated[str, Form()],
    file: Annotated[UploadFile | None, File()] = None,
    expected_version: Annotated[int | None, Form(ge=1)] = None,
    remove_attachment: Annotated[bool, Form()] = False,
):
    try:
        payload = draft_adapter.validate_json(draft)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors(include_input=False, include_context=False)) from None
    attachment = None
    if file is not None:
        data = await file.read(MAX_PDF_BYTES + 1)
        attachment = (pdf_filename(file.filename, file.content_type, data), data)
    if attachment and remove_attachment:
        raise ApiError(422, "VALIDATION_ERROR", "Choose whether to replace or remove the attachment.")
    return payload, attachment, expected_version, remove_attachment


def download(row):
    if row is None or not row.attachment_name:
        raise ApiError(404, "NOT_FOUND", "PDF attachment not found.")
    return Response(
        row.attachment,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{row.attachment_name}"'},
    )


@router.get("/learning-skills")
def skills(
    limit: Limit = 20,
    offset: Offset = 0,
    q: Annotated[str | None, Query(max_length=80)] = None,
    s=Depends(service),
):
    return s.skills(limit, offset, q)


@router.get("/instructor/learning")
def mine(limit: Limit = 20, offset: Offset = 0, s=Depends(service)):
    return s.page(limit, offset)


@router.post("/instructor/learning", status_code=201, dependencies=[Depends(require_csrf)])
def create(s=Depends(service), data=Depends(form)):
    draft, attachment, version, remove = data
    if version is not None or remove:
        raise ApiError(422, "VALIDATION_ERROR", "New drafts cannot replace existing content.")
    return s.save(draft, attachment)


@router.get("/instructor/learning/{id}")
def mine_detail(id: UUID, s=Depends(service)):
    return s.detail(s.row(id))


@router.put("/instructor/learning/{id}", dependencies=[Depends(require_csrf)])
def update(id: UUID, s=Depends(service), data=Depends(form)):
    draft, attachment, version, remove = data
    if version is None:
        raise ApiError(422, "VALIDATION_ERROR", "A draft version is required.")
    return s.save(draft, attachment, id=id, version=version, remove_attachment=remove)


@router.post("/instructor/learning/{id}/submit", dependencies=[Depends(require_csrf)])
def submit(id: UUID, payload: SubmissionVersion, s=Depends(service)):
    return s.submit(id, payload.expected_version)


@router.get("/instructor/learning/{id}/attachment")
def mine_attachment(id: UUID, s=Depends(service)):
    return download(s.row(id, lock=True))


@router.get("/admin/learning-submissions")
def queue(
    status: Literal["pending", "approved", "changes_requested"] = "pending",
    limit: Limit = 20,
    offset: Offset = 0,
    s=Depends(service),
):
    return s.page(limit, offset, admin=True, status=status)


@router.get("/admin/learning-submissions/{id}")
def preview(id: UUID, s=Depends(service)):
    return s.detail(s.row(id, admin=True))


@router.get("/admin/learning-submissions/{id}/attachment")
def review_attachment(id: UUID, s=Depends(service)):
    return download(s.row(id, admin=True, lock=True))


@router.patch("/admin/learning-submissions/{id}", dependencies=[Depends(require_csrf)])
def review(id: UUID, payload: ReviewDecision, s=Depends(service)):
    return s.review(id, payload)


@router.get("/content/{id}/attachment")
def published_attachment(id: UUID, s=Depends(service)):
    s.learning.content(id, public_only=True, lock=True)
    return download(s.published_materials(id))

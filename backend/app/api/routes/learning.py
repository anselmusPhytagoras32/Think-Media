"""FR03/10/11 authenticated learning, moderation and guidance HTTP adapters."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_csrf
from app.errors import ApiError
from app.models import User
from app.schemas.learning import (
    AssistantInput,
    ContentInput,
    ContentPatch,
    QuizInput,
    ReactInput,
    ReportInput,
    ResolveInput,
    SaveInput,
)
from app.services.assistant import AssistantService
from app.services.bundled_guidance import guide_detail
from app.services.learning import LearningService
from app.services.learning_submissions import SubmissionService
from app.services.assistant_workspace import WorkspaceAssistant

router = APIRouter(tags=["learning"])
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


def service(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return LearningService(db, user)


@router.get("/content")
def feed(
    q: Annotated[str | None, Query(max_length=200)] = None,
    tag: Annotated[str | None, Query(max_length=80)] = None,
    limit: Limit = 20,
    offset: Offset = 0,
    s=Depends(service),
):
    return s.feed(limit, offset, q, tag)


@router.get("/content/{id}")
def detail(id: UUID, s=Depends(service)):
    output = s.out(s.content(id))
    materials = SubmissionService(s.db, s.user).published_materials(id)
    if materials:
        output.update(links=materials.payload["links"], attachment_name=materials.attachment_name)
    return output


@router.get("/admin/content")
def admin_feed(
    q: Annotated[str | None, Query(max_length=200)] = None,
    tag: Annotated[str | None, Query(max_length=80)] = None,
    status: Literal["draft", "published", "archived"] | None = None,
    limit: Limit = 20,
    offset: Offset = 0,
    s=Depends(service),
):
    return s.feed(limit, offset, q=q, tag=tag, admin=True, status=status)


@router.post("/admin/content", status_code=201, dependencies=[Depends(require_csrf)])
def create(payload: ContentInput, s=Depends(service)):
    return s.create(payload)


@router.patch("/admin/content/{id}", dependencies=[Depends(require_csrf)])
def edit(id: UUID, payload: ContentPatch, s=Depends(service)):
    return s.edit(id, payload)


@router.post("/content/{id}/save", dependencies=[Depends(require_csrf)])
def save(id: UUID, payload: SaveInput, s=Depends(service)):
    return s.state(id, "saved", payload.saved)


@router.post("/content/{id}/react", dependencies=[Depends(require_csrf)])
def react(id: UUID, payload: ReactInput, s=Depends(service)):
    return s.state(id, "reacted", payload.reacted)


@router.get("/content/{id}/quiz")
def quiz(id: UUID, s=Depends(service)):
    return s.quiz(id)


@router.post("/content/{id}/quiz", dependencies=[Depends(require_csrf)])
def answer(id: UUID, payload: QuizInput, s=Depends(service)):
    return s.answer(id, payload)


@router.post("/reports", status_code=201, dependencies=[Depends(require_csrf)])
def report(payload: ReportInput, s=Depends(service)):
    return s.report(payload)


@router.get("/admin/reports")
def reports(
    status: Literal["pending", "resolved"] = "pending",
    limit: Limit = 20,
    offset: Offset = 0,
    s=Depends(service),
):
    return s.reports(status, limit, offset)


@router.patch("/admin/reports/{id}", dependencies=[Depends(require_csrf)])
def resolve(id: UUID, payload: ResolveInput, s=Depends(service)):
    return s.resolve(id, payload)


@router.get("/admin/content-events")
def events(limit: Limit = 20, offset: Offset = 0, s=Depends(service)):
    return s.events(limit, offset)


@router.get("/assistant/sources/{slug}")
def bundled_source(slug: str, _user: User = Depends(get_current_user)):
    # Versioned public editorial help is available after local data resets.
    source = guide_detail(slug)
    if source is None:
        raise ApiError(404, "NOT_FOUND", "Resource not found.")
    return source


@router.post("/assistant", dependencies=[Depends(require_csrf)])
def assistant(
    payload: AssistantInput,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.workspace:
        return WorkspaceAssistant(
            db, user, request.state.session_row,
            request.app.state.assistant_provider, request.app.state.assistant_throttle,
            request.app.state.settings,
        ).answer(payload.question, payload.page, payload.previous_questions, payload.resource_id)
    return AssistantService(
        db, request.app.state.assistant_provider, request.app.state.assistant_throttle
    ).answer(payload.question, user.id, payload.previous_questions)


@router.post("/assistant/actions/{id}/confirm", dependencies=[Depends(require_csrf)])
def confirm_assistant_action(id: UUID, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return WorkspaceAssistant(db, user, request.state.session_row, request.app.state.assistant_provider,
                              request.app.state.assistant_throttle, request.app.state.settings).consume(id)


@router.post("/assistant/actions/{id}/cancel", dependencies=[Depends(require_csrf)])
def cancel_assistant_action(id: UUID, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return WorkspaceAssistant(db, user, request.state.session_row, request.app.state.assistant_provider,
                              request.app.state.assistant_throttle, request.app.state.settings).consume(id, cancel=True)


@router.get("/assistant/capabilities")
def assistant_capabilities(request: Request, user: User = Depends(get_current_user)):
    prompts = {
        "student": [("Find OJT", "Find published OJT opportunities"), ("Find lessons", "Find resume preparation lessons"), ("My applications", "Open my applications")],
        "instructor": [("Draft a lesson", "Draft a short OJT interview lesson with one quiz question"), ("Draft a skill", "Draft a workplace communication skill category"), ("My materials", "Open my teaching materials")],
        "company": [("My listings", "Open my company listings"), ("Draft a listing", "Draft a fictional React OJT listing in Legazpi City"), ("Review applicants", "Open my applicant review workspace")],
        "administrator": [("Verify companies", "Open company verification"), ("Review learning", "Open instructor submission review"), ("Audit", "Open the audit workspace")],
    }
    return {"actions_available": request.app.state.settings.assistant_tools_enabled and hasattr(request.app.state.assistant_provider, "plan"),
            "prompts": [{"label": label, "question": question} for label, question in prompts[user.role]]}

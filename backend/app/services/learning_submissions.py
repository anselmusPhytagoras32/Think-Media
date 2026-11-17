"""FR03/11 ownership, review transitions and transactional publication."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.enums import Role
from app.errors import ApiError
from app.models import LearningReview, LearningSubmission
from app.schemas.learning import ContentInput
from app.schemas.learning_submission import LessonDraft, draft_adapter
from app.services.learning import LearningService
from app.time_utils import iso_manila


EDITABLE = {"draft", "changes_requested"}


class SubmissionService:
    def __init__(self, db, user):
        self.db = db
        self.user = user
        self.learning = LearningService(db, user)

    def instructor(self):
        if self.user.role != Role.INSTRUCTOR:
            raise ApiError(403, "FORBIDDEN", "An instructor account is required.")

    def row(self, id, *, admin=False, lock=False):
        query = select(LearningSubmission).where(LearningSubmission.id == id)
        if admin:
            self.learning.admin()
            query = query.where(LearningSubmission.status != "draft")
        else:
            self.instructor()
            query = query.where(LearningSubmission.author_id == self.user.id)
        row = self.db.scalar(query.with_for_update() if lock else query)
        if row is None:
            raise ApiError(404, "NOT_FOUND", "Submission not found.")
        return row

    @staticmethod
    def summary(row):
        return dict(
            id=str(row.id),
            kind=row.kind,
            title=row.payload["title"],
            summary=row.payload["summary"],
            status=row.status,
            version=row.version,
            updated_at=iso_manila(row.updated_at),
        )

    def detail(self, row):
        reviews = self.db.scalars(
            select(LearningReview)
            .where(LearningReview.submission_id == row.id)
            .order_by(LearningReview.submitted_version.desc())
            .limit(1)
        ).first()
        return dict(
            **self.summary(row),
            draft=row.payload,
            skills=self.selected_skills(row.payload.get("skill_ids", [])),
            attachment_name=row.attachment_name,
            published_content_id=str(row.published_content_id) if row.published_content_id else None,
            review=dict(
                decision=reviews.decision,
                feedback=reviews.feedback,
                reviewed_at=iso_manila(reviews.created_at),
            ) if reviews else None,
        )

    def page(self, limit, offset, *, admin=False, status=None):
        query = select(LearningSubmission)
        if admin:
            self.learning.admin()
            query = query.where(LearningSubmission.status == status)
        else:
            self.instructor()
            query = query.where(LearningSubmission.author_id == self.user.id)
        return self.learning.page(
            query.order_by(LearningSubmission.updated_at.desc(), LearningSubmission.id),
            limit,
            offset,
            self.summary,
        )

    @staticmethod
    def approved_skills():
        return select(LearningSubmission).where(LearningSubmission.approved_skill_key.is_not(None))

    def skills(self, limit, offset, q):
        query = self.approved_skills()
        if q:
            query = query.where(LearningSubmission.approved_skill_key.icontains(q.casefold(), autoescape=True))
        return self.learning.page(
            query.order_by(LearningSubmission.approved_skill_key, LearningSubmission.id),
            limit,
            offset,
            lambda row: dict(id=str(row.id), name=row.payload["title"], description=row.payload["summary"]),
        )

    def selected_skills(self, skill_ids):
        if not skill_ids:
            return []
        ids = [UUID(str(id)) for id in skill_ids]
        rows = self.db.scalars(self.approved_skills().where(LearningSubmission.id.in_(ids)))
        names = {row.id: row.payload["title"] for row in rows}
        if len(names) != len(skill_ids):
            raise ApiError(422, "INVALID_SKILL", "Select only approved skill categories.")
        return [dict(id=str(id), name=names[id]) for id in ids]

    @staticmethod
    def check_version(row, expected, statuses):
        if row.version != expected or row.status not in statuses:
            raise ApiError(409, "SUBMISSION_CONFLICT", "This submission changed. Reopen it and try again.")

    def save(self, draft, attachment, *, id=None, version=None, remove_attachment=False):
        self.instructor()
        if isinstance(draft, LessonDraft):
            self.selected_skills(draft.skill_ids)
        elif attachment or remove_attachment:
            raise ApiError(422, "INVALID_UPLOAD", "Only lessons can have attachments.")

        if id is None:
            row = LearningSubmission(author_id=self.user.id, kind=draft.kind)
            self.db.add(row)
        else:
            row = self.row(id, lock=True)
            self.check_version(row, version, EDITABLE)
            if row.kind != draft.kind:
                raise ApiError(422, "VALIDATION_ERROR", "A submission's type cannot change.")
            row.version += 1
        row.payload = draft.model_dump(mode="json")
        if attachment:
            row.attachment_name, row.attachment = attachment
        elif remove_attachment:
            row.attachment_name = row.attachment = None
        self.db.commit()
        return self.detail(row)

    def submit(self, id, expected):
        row = self.row(id, lock=True)
        self.check_version(row, expected, EDITABLE)
        row.status = "pending"
        row.version += 1
        self.db.commit()
        return self.detail(row)

    def review(self, id, decision):
        row = self.row(id, admin=True, lock=True)
        try:
            self.stage_review(row, decision)
            self.db.commit()
        except IntegrityError as exc:
            if getattr(getattr(exc.orig, "diag", None), "constraint_name", None) != (
                "uq_learning_submissions_approved_skill_key"
            ):
                raise
            self.db.rollback()
            raise ApiError(409, "SKILL_EXISTS", "A skill category with this name is already approved.") from None
        return self.detail(row)

    def stage_review(self, row, decision):
        self.learning.admin()
        self.check_version(row, decision.expected_version, {"pending"})
        self.db.add(LearningReview(
            submission_id=row.id,
            submitted_version=row.version,
            reviewer_id=self.user.id,
            decision=decision.decision,
            feedback=decision.feedback,
        ))
        if decision.decision == "approved":
            if row.kind == "lesson":
                draft = draft_adapter.validate_python(row.payload)
                categories = self.selected_skills(draft.skill_ids)
                tags = list(dict.fromkeys(draft.tags + [skill["name"] for skill in categories]))
                content = self.learning.add_content(
                    ContentInput(
                        title=draft.title, summary=draft.summary, body=draft.body,
                        tags=tags, questions=draft.questions, status="published",
                    ),
                    row.author_id,
                )
                row.published_content_id = content.id
            else:
                row.approved_skill_key = row.payload["title"].casefold()
        row.status = decision.decision
        row.version += 1

    def published_materials(self, content_id):
        return self.db.scalar(
            select(LearningSubmission).where(LearningSubmission.published_content_id == content_id)
        )

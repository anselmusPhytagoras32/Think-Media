"""FR03/11 learning publication, scoring, preferences and audited moderation."""

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.errors import ApiError
from app.models import (
    ContentEvent,
    ContentState,
    LearningContent,
    ModerationReport,
    QuizAttempt,
    QuizQuestion,
)
from app.repositories.learning import ContentRepository
from app.schemas.learning import ContentInput
from app.services.content_cache import public_content_cache
from app.time_utils import iso_manila, utcnow


class LearningService:
    def __init__(self, db, user):
        self.db = db
        self.user = user
        self.repo = ContentRepository(db)

    def admin(self):
        if self.user.role != "administrator":
            raise ApiError(403, "FORBIDDEN", "Administrator privileges are required.")

    def learner(self):
        if self.user.role not in {"student", "instructor"}:
            raise ApiError(
                403, "FORBIDDEN", "A student or instructor account is required."
            )

    def content(self, id, public_only=False, lock=False):
        row = self.repo.get(id, lock)
        if (
            row is None
            or row.status != "published"
            and (public_only or self.user.role != "administrator")
        ):
            raise ApiError(404, "NOT_FOUND", "Resource not found.")
        return row

    def out(self, row):
        # FR03/11, NFR03/11: callers have fetched/authorized the current row.
        # A versioned public projection can be shared; private flags cannot.
        bind = self.db.get_bind()
        engine = getattr(bind, "engine", bind)
        key = (engine, row.id, row.updated_at, row.status)
        projection = public_content_cache.get(key) if row.status == "published" else None
        if projection is None:
            projection = dict(
                id=str(row.id),
                title=row.title,
                summary=row.summary,
                body=row.body,
                tags=list(row.tags),
                status=row.status,
                created_at=iso_manila(row.created_at),
                updated_at=iso_manila(row.updated_at),
                has_quiz=bool(self.repo.questions(row.id)),
            )
            if row.status == "published":
                public_content_cache.put(key, projection)
        state = self.db.get(ContentState, (self.user.id, row.id))
        return dict(
            **projection,
            saved=bool(state and state.saved),
            reacted=bool(state and state.reacted),
        )

    def page(self, query, limit, offset, presenter):
        rows, total = self.repo.page(query, limit, offset)
        return dict(
            items=[presenter(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def feed(self, limit, offset, q=None, tag=None, admin=False, status=None):
        query = select(LearningContent)
        if admin:
            self.admin()
            if status:
                query = query.where(LearningContent.status == status)
        else:
            query = query.where(LearningContent.status == "published")
        if q:
            query = query.where(
                LearningContent.title.icontains(q, autoescape=True)
                | LearningContent.summary.icontains(q, autoescape=True)
            )
        if tag:
            query = query.where(LearningContent.tags.any(tag))
        return self.page(
            query.order_by(LearningContent.created_at.desc(), LearningContent.id),
            limit,
            offset,
            self.out,
        )

    def create(self, payload):
        self.admin()
        row = LearningContent(
            author_id=self.user.id, **payload.model_dump(exclude={"questions"})
        )
        self.db.add(row)
        self.db.flush()
        for position, item in enumerate(payload.questions):
            self.db.add(
                QuizQuestion(content_id=row.id, position=position, **item.model_dump())
            )
        self.repo.add_event(row.id, self.user.id, "created", row.status)
        self.db.commit()
        return self.out(row)

    def edit(self, id, payload):
        self.admin()
        row = self.content(id, lock=True)
        values = payload.model_dump(exclude_unset=True)
        if not values or any(value is None for value in values.values()):
            raise ApiError(422, "VALIDATION_ERROR", "Provide editable non-null fields.")
        merged = {
            key: getattr(row, key) for key in ("title", "summary", "body", "tags")
        }
        merged.update({key: value for key, value in values.items() if key != "status"})
        try:
            valid = ContentInput.model_validate(merged)
        except ValidationError:
            raise ApiError(
                422, "VALIDATION_ERROR", "Resource fields are invalid."
            ) from None
        old = row.status
        for key in merged:
            setattr(row, key, getattr(valid, key))
        if "status" in values:
            row.status = values["status"]
        self.repo.add_event(row.id, self.user.id, "updated", f"{old} -> {row.status}")
        self.db.commit()
        return self.out(row)

    def state(self, id, field, value):
        self.learner()
        row = self.content(id, public_only=True, lock=True)
        statement = insert(ContentState).values(
            user_id=self.user.id, content_id=id, saved=False, reacted=False
        )
        statement = statement.on_conflict_do_nothing(
            index_elements=["user_id", "content_id"]
        )
        self.db.execute(statement)
        state = self.db.get(ContentState, (self.user.id, id))
        setattr(state, field, value)
        self.db.commit()
        return self.out(row)

    def quiz(self, id):
        self.learner()
        self.content(id, public_only=True)
        return dict(
            questions=[
                dict(id=str(row.id), question=row.question, options=row.options)
                for row in self.repo.questions(id)
            ]
        )

    def answer(self, id, payload):
        self.learner()
        self.content(id, public_only=True, lock=True)
        questions = self.repo.questions(id)
        if not questions or set(payload.answers) != {q.id for q in questions}:
            raise ApiError(
                422, "VALIDATION_ERROR", "Answer every question exactly once."
            )
        if any(not 0 <= payload.answers[q.id] < len(q.options) for q in questions):
            raise ApiError(
                422, "VALIDATION_ERROR", "Choose a valid option for each question."
            )
        correct = sum(payload.answers[q.id] == q.correct_index for q in questions)
        total = len(questions)
        self.db.add(
            QuizAttempt(
                content_id=id,
                user_id=self.user.id,
                answers={str(key): value for key, value in payload.answers.items()},
                correct=correct,
                total=total,
            )
        )
        self.db.commit()
        return dict(score=round(100 * correct / total, 2), total=total, correct=correct)

    def report_out(self, row):
        return dict(
            id=str(row.id),
            content_id=str(row.content_id),
            reporter_id=str(row.reporter_id),
            reason=row.reason,
            status=row.status,
            resolution=row.resolution,
            resolved_by=str(row.resolved_by) if row.resolved_by else None,
            resolved_at=iso_manila(row.resolved_at) if row.resolved_at else None,
            created_at=iso_manila(row.created_at),
        )

    def report(self, payload):
        self.content(payload.content_id, public_only=True, lock=True)
        if not payload.reason.strip():
            raise ApiError(422, "VALIDATION_ERROR", "Enter a report reason.")
        row = ModerationReport(
            content_id=payload.content_id,
            reporter_id=self.user.id,
            reason=payload.reason.strip(),
        )
        self.db.add(row)
        self.db.flush()
        self.repo.add_event(row.content_id, self.user.id, "reported", str(row.id))
        self.db.commit()
        return self.report_out(row)

    def reports(self, status, limit, offset):
        self.admin()
        query = (
            select(ModerationReport)
            .where(ModerationReport.status == status)
            .order_by(ModerationReport.created_at, ModerationReport.id)
        )
        return self.page(query, limit, offset, self.report_out)

    def resolve(self, id, payload):
        self.admin()
        row = self.repo.report(id, lock=True)
        if row is None:
            raise ApiError(404, "NOT_FOUND", "Report not found.")
        if row.status != "pending":
            raise ApiError(
                409, "REPORT_RESOLVED", "This report has already been resolved."
            )
        if not payload.resolution.strip():
            raise ApiError(422, "VALIDATION_ERROR", "Enter a resolution.")
        row.status = "resolved"
        row.resolution = payload.resolution.strip()
        row.resolved_by = self.user.id
        row.resolved_at = utcnow()
        self.repo.add_event(
            row.content_id,
            self.user.id,
            "report_resolved",
            f"{row.id}: {row.resolution}",
        )
        self.db.commit()
        return self.report_out(row)

    def events(self, limit, offset):
        self.admin()

        def present(row):
            return dict(
                id=str(row.id),
                content_id=str(row.content_id),
                actor_id=str(row.actor_id),
                action=row.action,
                detail=row.detail,
                created_at=iso_manila(row.created_at),
            )

        return self.page(
            select(ContentEvent).order_by(
                ContentEvent.created_at.desc(), ContentEvent.id
            ),
            limit,
            offset,
            present,
        )

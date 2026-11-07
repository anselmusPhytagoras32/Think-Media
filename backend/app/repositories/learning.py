"""FR03/11 parameterized learning and event persistence."""

from sqlalchemy import func, select

from app.models import ContentEvent, LearningContent, ModerationReport, QuizQuestion


class ContentRepository:
    def __init__(self, db):
        self.db = db

    def get(self, id, lock=False):
        query = select(LearningContent).where(LearningContent.id == id)
        return self.db.scalar(query.with_for_update() if lock else query)

    def questions(self, id):
        return list(
            self.db.scalars(
                select(QuizQuestion)
                .where(QuizQuestion.content_id == id)
                .order_by(QuizQuestion.position)
            )
        )

    def page(self, query, limit, offset):
        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        return list(self.db.scalars(query.limit(limit).offset(offset))), total

    def add_event(self, content_id, actor_id, action, detail=""):
        self.db.add(
            ContentEvent(
                content_id=content_id, actor_id=actor_id, action=action, detail=detail
            )
        )
        self.db.flush()

    def report(self, id, lock=False):
        query = select(ModerationReport).where(ModerationReport.id == id)
        return self.db.scalar(query.with_for_update() if lock else query)

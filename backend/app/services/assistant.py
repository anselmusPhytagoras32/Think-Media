"""FR10 bounded approved-only retrieval and provider output validation."""

import re

from sqlalchemy import or_, select

from app.errors import ApiError
from app.models import LearningContent


class AssistantService:
    def __init__(self, db, provider, throttle):
        self.db = db
        self.provider = provider
        self.throttle = throttle

    def answer(self, question, user_id):
        question = question.strip()
        if not question:
            raise ApiError(422, "VALIDATION_ERROR", "Enter a question.")
        retry = self.throttle.retry_after(str(user_id))
        if retry is not None:
            raise ApiError(
                429,
                "RATE_LIMITED",
                "Too many assistant requests. Try again later.",
                headers={"Retry-After": str(retry)},
            )
        self.throttle.record_attempt(str(user_id))
        # The provider receives no actor, profile, session or marketplace records.
        words = list(dict.fromkeys(re.findall(r"[\w]{3,}", question.casefold())))[:12]
        sources = []
        if words:
            matches = [
                LearningContent.title.icontains(word, autoescape=True)
                | LearningContent.summary.icontains(word, autoescape=True)
                | LearningContent.body.icontains(word, autoescape=True)
                for word in words
            ]
            rows = self.db.scalars(
                select(LearningContent)
                .where(LearningContent.status == "published", or_(*matches))
                .order_by(LearningContent.created_at.desc(), LearningContent.id)
                .limit(3)
            )
            sources = [
                dict(id=str(row.id), title=row.title, excerpt=row.body[:800])
                for row in rows
            ]
        try:
            output = self.provider.respond(question, sources)
            if (
                not isinstance(output, dict)
                or not isinstance(output.get("answer"), str)
                or not 1 <= len(output["answer"]) <= 8000
                or type(output.get("uncertainty")) is not bool
                or output.get("mode") not in {"retrieval", "external"}
            ):
                raise ValueError("Invalid provider output.")
            citations = output.get("sources")
            if not isinstance(citations, list) or len(citations) > 3:
                raise ValueError("Invalid citations.")
            approved = {source["id"]: source["title"] for source in sources}
            if any(
                not isinstance(source, dict) or source.get("id") not in approved
                for source in citations
            ):
                raise ValueError("Unapproved citation.")
            return dict(
                answer=output["answer"],
                sources=[
                    dict(id=source["id"], title=approved[source["id"]])
                    for source in citations
                ],
                uncertainty=output["uncertainty"] or not citations,
                mode=output["mode"],
            )
        except Exception:
            # Provider exceptions and malformed responses never expose secrets.
            raise ApiError(
                503,
                "ASSISTANT_UNAVAILABLE",
                "The assistant is unavailable. You can still browse resources and manage applications.",
            ) from None

"""FR10 bounded approved-only retrieval and provider output validation."""

from app.errors import ApiError
from app.services.guidance_retrieval import retrieve_sources


class AssistantService:
    def __init__(self, db, provider, throttle):
        self.db = db
        self.provider = provider
        self.throttle = throttle

    def answer(self, question, user_id, previous_questions=None):
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
        history = previous_questions or []
        sources = retrieve_sources(self.db, question, history)
        try:
            output = self.provider.respond(question, sources, previous_questions=history) if history else self.provider.respond(question, sources)
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

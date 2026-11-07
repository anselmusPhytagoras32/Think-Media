"""FR10 read-only provider boundary: only question and approved excerpts.

No external LLM provider is configured or claimed by this implementation.
"""

from typing import Protocol


class AssistantUnavailable(Exception):
    pass


class AssistantProvider(Protocol):
    def respond(self, question: str, sources: list[dict]) -> dict: ...


class DisabledProvider:
    def respond(self, question, sources):
        raise AssistantUnavailable("The assistant provider is disabled.")


class RetrievalProvider:
    def respond(self, question, sources):
        if not sources:
            return dict(
                answer="Resource lookup found no approved resources matching your question. Try a different topic.",
                sources=[],
                uncertainty=True,
                mode="retrieval",
            )
        return dict(
            answer="Resource lookup — excerpts from approved learning resources:\n\n"
            + "\n\n".join(
                f"{source['title']}: {source['excerpt']}" for source in sources
            ),
            sources=[
                dict(id=source["id"], title=source["title"]) for source in sources
            ],
            uncertainty=True,
            mode="retrieval",
        )


def provider_for(mode):
    return RetrievalProvider() if mode == "retrieval" else DisabledProvider()

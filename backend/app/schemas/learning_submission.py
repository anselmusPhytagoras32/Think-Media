"""Strict, bounded instructor authoring payloads (FR03/11)."""

from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import Field, StrictInt, StringConstraints, TypeAdapter, field_validator, model_validator

from app.schemas.learning import QuestionInput
from app.schemas.models import ApiModel
from app.validation import normalize_string_list

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Summary = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class ResourceLink(ApiModel):
    label: ShortText
    url: str = Field(max_length=2048)

    @field_validator("url")
    @classmethod
    def check_url(cls, value):
        value = value.strip()
        if any(character.isspace() or ord(character) < 32 for character in value) or "\\" in value:
            raise ValueError("Use a valid HTTP or HTTPS URL.")
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username is not None:
            raise ValueError("Use a valid HTTP or HTTPS URL without credentials.")
        return value


class LessonDraft(ApiModel):
    kind: Literal["lesson"]
    title: ShortText
    summary: Summary
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)]
    tags: list[str] = Field(default_factory=list, max_length=30)
    skill_ids: list[UUID] = Field(default_factory=list, max_length=30)
    links: list[ResourceLink] = Field(default_factory=list, max_length=10)
    questions: list[QuestionInput] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def check_tags(self):
        self.tags = normalize_string_list(self.tags, field="Tags")
        if len(self.tags) + len(self.skill_ids) > 30 or len(set(self.skill_ids)) != len(self.skill_ids):
            raise ValueError("Use up to 30 tags and distinct skill categories in total.")
        return self


class SkillDraft(ApiModel):
    kind: Literal["skill"]
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    summary: Summary


Draft = Annotated[LessonDraft | SkillDraft, Field(discriminator="kind")]
draft_adapter = TypeAdapter(Draft)


class SubmissionVersion(ApiModel):
    expected_version: StrictInt = Field(ge=1)


class ReviewDecision(SubmissionVersion):
    decision: Literal["approved", "changes_requested"]
    feedback: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] = ""

    @model_validator(mode="after")
    def explain_changes(self):
        if self.decision == "changes_requested" and not self.feedback:
            raise ValueError("Explain what the instructor should change.")
        return self

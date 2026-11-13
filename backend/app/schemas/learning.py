"""FR03/10/11 bounded strict learning and guidance input."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StrictBool, StrictInt, field_validator, model_validator

from app.schemas.models import ApiModel
from app.validation import normalize_string_list


class QuestionInput(ApiModel):
    question: str = Field(min_length=1, max_length=1000)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_index: StrictInt = Field(ge=0, le=5)

    @model_validator(mode="after")
    def check_options(self):
        if not self.question.strip() or any(
            not option.strip() or len(option) > 1000 for option in self.options
        ):
            raise ValueError("Question and options must contain bounded text.")
        if self.correct_index >= len(self.options):
            raise ValueError("Correct index is outside available options.")
        return self


class ContentInput(ApiModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=20000)
    tags: list[str] = Field(default_factory=list, max_length=30)
    status: Literal["draft", "published"] = "draft"
    questions: list[QuestionInput] = Field(default_factory=list, max_length=20)

    @field_validator("title", "summary", "body")
    @classmethod
    def trim(cls, value):
        if not value.strip():
            raise ValueError("This field is required.")
        return value.strip()

    @field_validator("tags")
    @classmethod
    def check_tags(cls, value):
        return normalize_string_list(value, field="Tags")


class ContentPatch(ApiModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = Field(default=None, min_length=1, max_length=500)
    body: str | None = Field(default=None, min_length=1, max_length=20000)
    tags: list[str] | None = Field(default=None, max_length=30)
    status: Literal["draft", "published", "archived"] | None = None


class SaveInput(ApiModel):
    saved: StrictBool


class ReactInput(ApiModel):
    reacted: StrictBool


class QuizInput(ApiModel):
    answers: dict[UUID, StrictInt] = Field(max_length=20)


class ReportInput(ApiModel):
    content_id: UUID
    reason: str = Field(min_length=1, max_length=1000)


class ResolveInput(ApiModel):
    status: Literal["resolved"]
    resolution: str = Field(min_length=1, max_length=1000)


class AssistantInput(ApiModel):
    question: str = Field(min_length=1, max_length=2000)
    previous_questions: list[Annotated[str, Field(min_length=1, max_length=1000)]] = Field(default_factory=list, max_length=3)

    @field_validator('previous_questions')
    @classmethod
    def nonempty_context(cls, value):
        if any(not question.strip() for question in value):
            raise ValueError('Previous questions must not be empty.')
        return [question.strip() for question in value]

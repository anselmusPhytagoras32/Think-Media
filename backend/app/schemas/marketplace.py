"""FR04–07 strict bounded API input contracts."""

from typing import Literal

from pydantic import Field, field_validator

from app.schemas.models import ApiModel
from app.validation import normalize_string_list


class ListingInput(ApiModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    requirements: str = Field(min_length=1, max_length=10000)
    location: str = Field(min_length=1, max_length=200)
    type: Literal["ojt", "job"]
    skills: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("title", "description", "requirements", "location")
    @classmethod
    def trim(cls, value):
        if not value.strip():
            raise ValueError("This field is required.")
        return value.strip()

    @field_validator("skills")
    @classmethod
    def skills_valid(cls, value):
        return normalize_string_list(value, field="Skills")


class ListingPatch(ApiModel):
    title: str | None = None
    description: str | None = None
    requirements: str | None = None
    location: str | None = None
    type: Literal["ojt", "job"] | None = None
    skills: list[str] | None = None


class StatusInput(ApiModel):
    status: Literal["under_review", "accepted", "rejected"]

"""FR09 ratings are explicit, optional and strictly numeric integers."""

from typing import Literal
from uuid import UUID

from pydantic import Field, StrictInt, model_validator

from app.schemas.models import ApiModel


class InteractionInput(ApiModel):
    item_type: Literal["listing", "content"]
    item_id: UUID
    event_type: Literal["view", "rating"]
    rating: StrictInt | None = Field(default=None, ge=1, le=5)

    @model_validator(mode="after")
    def appropriate_rating(self):
        if self.event_type == "rating" and self.rating is None:
            raise ValueError("Choose an explicit rating from 1 to 5.")
        if self.event_type == "view" and self.rating is not None:
            raise ValueError("Views must not contain ratings.")
        return self

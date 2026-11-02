from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MovieReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=120)
    sentiment: Literal["positive", "negative", "mixed"]
    key_points: list[str] = Field(min_length=2, max_length=3)

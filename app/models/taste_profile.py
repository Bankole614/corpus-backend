from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DescriptiveWord(str, Enum):
    minimal = "minimal"
    bold = "bold"
    detailed = "detailed"
    geometric = "geometric"
    illustrative = "illustrative"
    traditional = "traditional"


class TasteProfileRequest(BaseModel):
    descriptive_words: list[DescriptiveWord] = Field(
        ..., min_length=1, max_length=6, description="Pick the words that draw you in most."
    )
    line_weight: Literal["fine", "bold"]
    color_approach: Literal["color", "black_grey"]
    composition: Literal["symmetrical", "organic"]


class TasteProfileResult(BaseModel):
    profile_id: str
    descriptive_words: list[DescriptiveWord]
    line_weight: Literal["fine", "bold"]
    color_approach: Literal["color", "black_grey"]
    composition: Literal["symmetrical", "organic"]
    summary: str = Field(
        ..., description="Plain-language recap of the style profile, for display and later matching."
    )

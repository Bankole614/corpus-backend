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
    japanese = "japanese"
    neo_traditional = "neo_traditional"
    realism = "realism"
    ornamental = "ornamental"
    watercolor = "watercolor"
    surrealist = "surrealist"
    lettering = "lettering"


class TasteProfileRequest(BaseModel):
    descriptive_words: list[DescriptiveWord] = Field(
        ..., min_length=1, max_length=15, description="Pick the words that draw you in most."
    )
    line_weight: str = Field(default="fine", description="Line weight preference (fine, bold, medium)")
    color_approach: str = Field(default="black_grey", description="Color preference (color, black_grey)")
    composition: str = Field(default="organic", description="Composition flow (symmetrical, organic, flowing, radial, etc.)")


class StyleCardItem(BaseModel):
    id: str
    image_url: str
    title: str
    word: DescriptiveWord
    line_weight: str = "fine"
    color_approach: str = "black_grey"
    composition: str = "organic"


class TasteProfileResult(BaseModel):
    profile_id: str
    descriptive_words: list[DescriptiveWord]
    line_weight: str = "fine"
    color_approach: str = "black_grey"
    composition: str = "organic"
    summary: str = Field(
        ..., description="Plain-language recap of the style profile, for display and later matching."
    )


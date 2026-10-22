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
    liked_card_ids: list[str] = Field(default_factory=list, description="IDs of cards swiped right or saved in the deck")


class StyleCardItem(BaseModel):
    id: str
    image_url: str
    title: str
    word: DescriptiveWord
    line_weight: str = "fine"
    color_approach: str = "black_grey"
    composition: str = "organic"


class TasteAestheticTraits(BaseModel):
    primary_style: str
    secondary_styles: list[str] = Field(default_factory=list)
    density: str
    contrast: str
    mood_keywords: list[str] = Field(default_factory=list)


class TasteConsultationAdvice(BaseModel):
    what_to_ask_for: list[str] = Field(default_factory=list)
    what_to_avoid: list[str] = Field(default_factory=list)
    key_terms: list[str] = Field(default_factory=list)


class TastePlacementInsights(BaseModel):
    recommended_placements: list[str] = Field(default_factory=list)
    aging_considerations: str


class TasteProfileResult(BaseModel):
    profile_id: str
    descriptive_words: list[DescriptiveWord]
    line_weight: str = "fine"
    color_approach: str = "black_grey"
    composition: str = "organic"
    archetype: str = "The Eclectic Collector"
    archetype_subtitle: str = "A bespoke visual dialogue balancing distinct tattoo traditions."
    summary: str = Field(
        ..., description="Plain-language recap of the style profile, for display and later matching."
    )
    narrative: str = Field(
        default="", description="Deep multi-paragraph editorial critique exploring the user's aesthetic synthesis."
    )
    aesthetic_traits: TasteAestheticTraits = Field(
        default_factory=lambda: TasteAestheticTraits(
            primary_style="Versatile",
            secondary_styles=[],
            density="Balanced",
            contrast="Medium",
            mood_keywords=[],
        )
    )
    consultation_advice: TasteConsultationAdvice = Field(default_factory=TasteConsultationAdvice)
    placement_insights: TastePlacementInsights = Field(
        default_factory=lambda: TastePlacementInsights(
            recommended_placements=[],
            aging_considerations="Protect healed tattoos with sunscreen to prevent fine linework degradation.",
        )
    )


class SaveStyleRequest(BaseModel):
    style_id: str = Field(..., min_length=1, max_length=100, description="Style card ID (e.g., 'deck_01')")


class SyncStyleRequest(BaseModel):
    saved_style_ids: list[str] = Field(default_factory=list, description="List of style card IDs to merge with cloud database")


class SavedStylesResponse(BaseModel):
    saved_style_ids: list[str]


class SavedStyleActionResponse(BaseModel):
    status: str = "success"


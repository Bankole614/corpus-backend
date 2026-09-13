from pydantic import BaseModel, Field

from app.models.taste_profile import DescriptiveWord


class ArtistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    contact_url: str = Field(..., description="Where to reach/follow them — Instagram, website, etc.")
    bio: str | None = Field(None, max_length=1000)
    style_tags: list[DescriptiveWord] = Field(..., min_length=1, max_length=6)
    line_weight: str = Field(..., pattern="^(fine|bold)$")
    color_approach: str = Field(..., pattern="^(color|black_grey)$")
    composition: str = Field(..., pattern="^(symmetrical|organic)$")


class ArtistOut(BaseModel):
    id: str
    name: str
    contact_url: str
    bio: str | None
    style_tags: list[DescriptiveWord]
    line_weight: str
    color_approach: str
    composition: str


class ArtistMatch(BaseModel):
    artist: ArtistOut
    match_score: int = Field(..., description="Higher is a closer style match. Not a percentage.")

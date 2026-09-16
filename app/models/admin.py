from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.models.artist import ArtistOut
from app.models.auth import UserOut
from app.models.taste_profile import DescriptiveWord


class AdminOverviewMetrics(BaseModel):
    total_users: int
    active_users: int
    total_verifications: int
    total_concierge_sessions: int
    total_concierge_messages: int
    total_taste_profiles: int
    total_artists: int
    verifications_by_language: dict[str, int] = Field(default_factory=dict)


class AdminUserItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    is_admin: bool
    is_active: bool
    google_id: str | None = None
    created_at: datetime
    verifications_count: int = 0
    sessions_count: int = 0


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None
    full_name: str | None = None


class AdminUserDetail(BaseModel):
    user: AdminUserItem
    recent_verifications: list[dict[str, Any]] = Field(default_factory=list)
    recent_sessions: list[dict[str, Any]] = Field(default_factory=list)
    recent_taste_profiles: list[dict[str, Any]] = Field(default_factory=list)


class AdminVerificationItem(BaseModel):
    id: str
    user_id: str | None = None
    user_email: str | None = None
    input_phrase: str
    language: str
    intended_meaning: str | None = None
    grammatically_valid: bool
    confidence: str
    corrected_phrase: str | None = None
    literal_translation: str
    recommendation: str
    created_at: datetime


class AdminConciergeSessionItem(BaseModel):
    session_id: str
    user_id: str | None = None
    user_email: str | None = None
    ready_for_brief: bool
    message_count: int
    created_at: datetime
    updated_at: datetime


class AdminArtistUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    contact_url: str | None = None
    bio: str | None = Field(None, max_length=1000)
    style_tags: list[DescriptiveWord] | None = None
    line_weight: str | None = Field(None, pattern="^(fine|bold)$")
    color_approach: str | None = Field(None, pattern="^(color|black_grey)$")
    composition: str | None = Field(None, pattern="^(symmetrical|organic)$")

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SessionSummaryOut(BaseModel):
    session_id: str
    ready_for_brief: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    image_url: Optional[str] = None


class ConciergeChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ..., min_length=1, description="Full conversation history so far, oldest first."
    )


class ConciergeChatResponse(BaseModel):
    reply: str
    ready_for_brief: bool = Field(
        ..., description="True once the assistant judges it has enough to generate a structured brief."
    )


class SessionCreateResponse(BaseModel):
    session_id: str


class AttachmentUploadResponse(BaseModel):
    image_url: str


class SendMessageRequest(BaseModel):
    content: Optional[str] = Field(default="", max_length=4000)
    image_url: Optional[str] = Field(
        default=None,
        description="Optional image URL or uploaded attachment path (e.g. /static/concierge/filename.jpg).",
    )


class SessionMessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    image_url: Optional[str] = None


class SessionDetailResponse(BaseModel):
    session_id: str
    ready_for_brief: bool
    messages: list[SessionMessageOut]


class BriefRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)


class TattooBrief(BaseModel):
    concept_summary: str
    suggested_styles: list[str]
    historical_or_cultural_context: Optional[str] = None
    placement_notes: Optional[str] = None
    visual_reference_notes: Optional[str] = Field(
        default=None,
        description="Visual observations or stylistic notes from any reference photos or anatomical placements shared.",
    )
    risks_or_considerations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(
        default_factory=list, description="Things still worth discussing with an artist directly."
    )


class BriefResponse(BaseModel):
    brief: TattooBrief


class SessionDeleteResponse(BaseModel):
    message: str
    session_id: str


class ClearSessionsResponse(BaseModel):
    message: str
    deleted_count: int

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


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


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class SessionMessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str


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
    risks_or_considerations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(
        default_factory=list, description="Things still worth discussing with an artist directly."
    )


class BriefResponse(BaseModel):
    brief: TattooBrief

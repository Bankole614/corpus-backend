from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class EarlyAccessRequest(BaseModel):
    email: EmailStr = Field(..., description="Subscriber email address")
    source: str = Field(default="landing_page", description="Source or campaign tag")


class EarlyAccessResponse(BaseModel):
    success: bool = True
    message: str = "You're on the list! We'll keep you updated."
    email: str


class EarlyAccessSubscriberOut(BaseModel):
    id: str
    email: str
    source: str
    ip_address: str | None = None
    created_at: datetime


class EarlyAccessListResponse(BaseModel):
    total: int
    subscribers: list[EarlyAccessSubscriberOut]

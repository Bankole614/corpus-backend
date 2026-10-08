from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class DemoRequestPayload(BaseModel):
    email: EmailStr = Field(..., description="Requester email address")
    name: str = Field(..., min_length=1, description="Requester full name")
    role: str = Field(default="Individual / Collector", description="Role/Segment (Collector, Artist, Studio, etc.)")
    notes: str | None = Field(default=None, description="Notes or questions (optional)")
    source: str = Field(default="landing_page", description="Source or campaign tag")


class DemoResponse(BaseModel):
    success: bool = True
    message: str = "Demo request received! We'll reach out shortly to schedule your walkthrough."
    email: str


class DemoRequestOut(BaseModel):
    id: str
    email: str
    name: str | None = None
    role: str | None = None
    notes: str | None = None
    source: str
    ip_address: str | None = None
    created_at: datetime


class DemoListResponse(BaseModel):
    total: int
    requests: list[DemoRequestOut]

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """Deliberately minimal — no auth model has been decided yet. This exists
    so ConciergeSession has somewhere to point once auth is designed; user_id
    on a session is nullable until then."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ConciergeSession(Base):
    __tablename__ = "concierge_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    ready_for_brief: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    messages: Mapped[list["ConciergeMessage"]] = relationship(
        back_populates="session", order_by="ConciergeMessage.created_at", cascade="all, delete-orphan"
    )


class ConciergeMessage(Base):
    __tablename__ = "concierge_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    session_id: Mapped[str] = mapped_column(ForeignKey("concierge_sessions.id"))
    role: Mapped[str] = mapped_column(String)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped["ConciergeSession"] = relationship(back_populates="messages")


class TasteProfile(Base):
    __tablename__ = "taste_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # Stored as a comma-separated string rather than a separate join table —
    # deliberately simple for a fixed, small enum set. Revisit if the word
    # list grows or needs per-word querying (e.g. for artist matching).
    descriptive_words: Mapped[str] = mapped_column(String)
    line_weight: Mapped[str] = mapped_column(String)
    color_approach: Mapped[str] = mapped_column(String)
    composition: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    name: Mapped[str] = mapped_column(String)
    contact_url: Mapped[str] = mapped_column(String)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Same comma-separated-string approach as TasteProfile.descriptive_words above —
    # small fixed enum set, not worth a join table yet.
    style_tags: Mapped[str] = mapped_column(String)
    line_weight: Mapped[str] = mapped_column(String)
    color_approach: Mapped[str] = mapped_column(String)
    composition: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    input_phrase: Mapped[str] = mapped_column(String)
    language: Mapped[str] = mapped_column(String)
    intended_meaning: Mapped[str | None] = mapped_column(Text, nullable=True)
    grammatically_valid: Mapped[bool] = mapped_column(Boolean)
    confidence: Mapped[str] = mapped_column(String)  # "high" | "medium" | "low"
    corrected_phrase: Mapped[str | None] = mapped_column(Text, nullable=True)
    literal_translation: Mapped[str] = mapped_column(Text)
    issues: Mapped[str] = mapped_column(Text, default="[]")  # JSON string array
    historical_usage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

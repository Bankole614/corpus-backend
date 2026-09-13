from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class VerificationRequest(BaseModel):
    phrase: str = Field(
        ..., min_length=1, max_length=500, description="The phrase, quote, word, or symbol to verify."
    )
    language: Optional[str] = Field(
        "auto",
        max_length=50,
        description="The target language (e.g. latin, japanese, arabic, sanskrit, french, english) or 'auto' for automatic detection.",
    )
    intended_meaning: Optional[str] = Field(
        None,
        max_length=1000,
        description="What the user wants the phrase to mean/represent — helps catch translations that are grammatically fine but semantically wrong.",
    )


class VerificationResult(BaseModel):
    id: Optional[str] = None
    input_phrase: str
    language: str = Field(..., description="Target or verified language.")
    detected_language: Optional[str] = Field(
        None, description="Automatically detected source or target language if 'auto' was used."
    )
    intended_meaning: Optional[str] = None
    grammatically_valid: bool
    confidence: Literal["high", "medium", "low"]
    corrected_phrase: Optional[str] = None
    literal_translation: str
    issues: list[str] = Field(default_factory=list)
    historical_usage_notes: Optional[str] = None
    recommendation: str
    created_at: Optional[datetime] = None
    disclaimer: str = (
        "This is an AI-assisted linguistic check grounded in rigorous grammar and cultural references, "
        "not a substitute for review by a native speaker or language scholar. For a permanent tattoo, "
        "we strongly recommend an independent human review before proceeding."
    )



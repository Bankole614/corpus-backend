from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SupportedLanguage(str, Enum):
    latin = "latin"
    classical_greek = "classical_greek"
    sanskrit = "sanskrit"


class VerificationRequest(BaseModel):
    phrase: str = Field(..., min_length=1, max_length=500, description="The phrase the user is considering, in English or already-translated form.")
    language: SupportedLanguage
    intended_meaning: Optional[str] = Field(
        None,
        max_length=1000,
        description="What the user wants the phrase to mean/represent — helps catch translations that are grammatically fine but semantically wrong.",
    )


class VerificationResult(BaseModel):
    input_phrase: str
    language: SupportedLanguage
    grammatically_valid: bool
    confidence: Literal["high", "medium", "low"]
    corrected_phrase: Optional[str] = None
    literal_translation: str
    issues: list[str] = Field(default_factory=list)
    historical_usage_notes: Optional[str] = None
    recommendation: str
    disclaimer: str = (
        "This is an AI-assisted check grounded in classical grammar references, "
        "not a substitute for review by a language scholar. For a permanent tattoo, "
        "we strongly recommend an independent human review before proceeding."
    )

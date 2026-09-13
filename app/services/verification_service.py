"""
Phrase verification service.

Design intent (see PRD section 6.2):
- We only cover dead/stable languages for v1 (Latin, Classical Greek, Sanskrit)
  because they have real, citable academic grammar references and a fixed
  grammar that an LLM can be grounded against reliably.
- The LLM is NOT trusted to freewheel. It is given explicit grounding
  instructions per language and required to flag its own uncertainty rather
  than guess confidently.
- TODO (post-MVP): replace the prompt-only grounding below with real
  retrieval against a reference corpus/dictionary API (e.g. Perseus Digital
  Library for Latin/Greek, a vetted Sanskrit grammar/dictionary source) so
  answers are grounded in retrieved text, not model memory alone.
"""

import json
import re

from google.genai import types

from app.core.config import settings
from app.core.llm_client import get_client
from app.models.verification import SupportedLanguage, VerificationRequest, VerificationResult

# Per-language grounding notes. These get injected into the system prompt so
# the model knows what kind of authority to reason like, and what its known
# failure modes are for that language.
_GROUNDING_NOTES: dict[SupportedLanguage, str] = {
    SupportedLanguage.latin: (
        "You are grounding your answer in Classical Latin grammar (the standard taught from "
        "authors like Cicero, Virgil, Caesar), not Medieval or Ecclesiastical Latin usage, unless "
        "the user's intent suggests otherwise. Common failure modes to actively check for: "
        "(1) word-for-word 'Google Translate' phrasing that ignores case/declension, "
        "(2) incorrect verb conjugation or subject-verb agreement, "
        "(3) wrong case ending for the grammatical role of a noun, "
        "(4) idioms that don't survive literal translation from English. "
        "If you are not highly confident, say so explicitly rather than guessing."
    ),
    SupportedLanguage.classical_greek: (
        "You are grounding your answer in Classical (Attic) Greek grammar, not Koine or Modern Greek, "
        "unless context suggests otherwise. Common failure modes: "
        "(1) mixing Modern Greek vocabulary/spelling into a Classical phrase, "
        "(2) incorrect case/declension for the word's grammatical role, "
        "(3) wrong accentuation or breathing marks changing the meaning, "
        "(4) literal English-to-Greek translation that isn't idiomatic. "
        "If you are not highly confident, say so explicitly rather than guessing."
    ),
    SupportedLanguage.sanskrit: (
        "You are grounding your answer in classical Sanskrit grammar (Paninian grammar tradition). "
        "Common failure modes: "
        "(1) incorrect Devanagari transliteration/spelling, "
        "(2) sandhi (sound-combination) errors between words, "
        "(3) incorrect declension or verb conjugation, "
        "(4) mantra or spiritual phrases used out of their proper context or garbled from popular "
        "but inaccurate sources. If you are not highly confident, say so explicitly rather than guessing."
    ),
}

_SYSTEM_PROMPT_TEMPLATE = """You are a careful, conservative classical-language verification assistant \
for a tattoo-decision app. The user is considering a PERMANENT tattoo, so accuracy and honesty about \
uncertainty matter more than being impressive or definitive.

{grounding_notes}

Respond with ONLY a valid JSON object matching exactly this schema:
{{
  "grammatically_valid": boolean,
  "confidence": "high" | "medium" | "low",
  "corrected_phrase": string or null,
  "literal_translation": string,
  "issues": [string, ...],
  "historical_usage_notes": string or null,
  "recommendation": string
}}

Rules:
- "confidence" reflects YOUR certainty, not the user's. Use "low" liberally if there's any ambiguity.
- "issues" should be empty only if you found genuinely nothing wrong.
- "recommendation" is a short, plain-language summary a non-expert can act on.
- Never fabricate a citation or historical source. If you reference historical usage, only do so if \
you are confident it's accurate; otherwise leave historical_usage_notes null.
- If the user's intended_meaning is provided and the phrase doesn't actually convey that meaning \
(even if grammatically valid), flag that clearly in "issues".
"""


def _clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _build_system_prompt(language: SupportedLanguage) -> str:
    return _SYSTEM_PROMPT_TEMPLATE.format(grounding_notes=_GROUNDING_NOTES[language])


def _build_user_prompt(req: VerificationRequest) -> str:
    parts = [f"Phrase to verify: {req.phrase}", f"Target language: {req.language.value}"]
    if req.intended_meaning:
        parts.append(f"User's intended meaning: {req.intended_meaning}")
    return "\n".join(parts)


class VerificationError(Exception):
    pass


async def verify_phrase(req: VerificationRequest) -> VerificationResult:
    try:
        client = get_client()
    except RuntimeError as e:
        raise VerificationError(str(e)) from e

    system_prompt = _build_system_prompt(req.language)
    user_prompt = _build_user_prompt(req)

    try:
        response = await client.aio.models.generate_content(
            model=settings.verification_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
    except Exception as e:
        raise VerificationError(f"Gemini API request failed: {e}") from e

    raw_text = _clean_json_text(response.text or "")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise VerificationError(f"Model did not return valid JSON: {e}\nRaw output: {raw_text}") from e

    return VerificationResult(
        input_phrase=req.phrase,
        language=req.language,
        grammatically_valid=parsed.get("grammatically_valid", False),
        confidence=parsed.get("confidence", "low"),
        corrected_phrase=parsed.get("corrected_phrase"),
        literal_translation=parsed.get("literal_translation", ""),
        issues=parsed.get("issues", []),
        historical_usage_notes=parsed.get("historical_usage_notes"),
        recommendation=parsed.get("recommendation", ""),
    )


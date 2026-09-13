"""
Phrase & Symbol Verification Service.

Supports all classical, foreign, and modern languages (Latin, Greek, Sanskrit,
Japanese, Arabic, French, Spanish, English, Gaelic, etc.) with automatic
language detection or target language verification.

Design & Safety principles:
- The user is considering a PERMANENT tattoo. Accuracy, spelling, grammar,
  script orthography, and cultural context are paramount.
- The model operates under conservative linguistic guardrails: it flags any
  grammatical errors, awkward literal translations, broken declensions,
  or character errors, and defaults confidence to "low" or "medium" whenever
  ambiguity or uncertainty exists.
"""

import json
from typing import Optional

from google.genai import types

from app.core.config import settings
from app.core.llm_client import get_client
from app.models.verification import VerificationRequest, VerificationResult

_SYSTEM_PROMPT = """You are an expert linguistic scholar and conservative verification assistant \
for a tattoo-decision app (Corpus). The user is considering a PERMANENT tattoo, so rigorous accuracy, \
grammatical correctness, idiomatic reality, and honesty about uncertainty are critical.

Your task:
1. Language Identification: If the user specified a language, verify against that standard. If the language is "auto" or unspecified, accurately detect the language and script (e.g. Classical Latin, Attic Greek, Sanskrit/Devanagari, Japanese Kanji/Hiragana, Arabic, French, Spanish, Old Norse, etc.).
2. Grammatical & Syntactic Audit:
   - Check case declensions, verb conjugations, noun-adjective agreement, gender, and syntax.
   - For Classical Latin: ground in Classical standards (Cicero, Virgil), checking noun declension cases and verb moods.
   - For Classical Greek: ground in Attic standards, verifying accents and breathing marks.
   - For Sanskrit: check Paninian grammar, Devanagari orthography, and sandhi rules.
   - For Japanese/Chinese: check Kanji/Hanzi stroke validity, nuances, and unintended slang meanings.
   - For Arabic: verify diacritics, root meanings, and calligraphy appropriateness.
   - For English/Modern languages: check spelling, grammar, author quote accuracy, and typography.
3. Idiomatic & Semantic Reality:
   - Identify word-for-word "Google Translate" phrasings that native or classical speakers would find unnatural.
   - If the user provides an "intended_meaning", verify whether the phrase genuinely expresses that concept.
4. Conservative Judgment:
   - If there is any doubt or ambiguity, report confidence as "low" or "medium".
   - Report issues clearly and concisely so a non-expert understands why a phrase might need correction.

Respond with ONLY a valid JSON object matching exactly this schema:
{
  "detected_language": string,
  "grammatically_valid": boolean,
  "confidence": "high" | "medium" | "low",
  "corrected_phrase": string or null,
  "literal_translation": string,
  "issues": [string, ...],
  "historical_usage_notes": string or null,
  "recommendation": string
}

Rules:
- "confidence" reflects YOUR scholarly certainty. Use "low" or "medium" liberally if there is any nuance or ambiguity.
- "issues" must list every grammatical error, unnatural word choice, or semantic mismatch. Only empty if completely flawless.
- "recommendation" is a short, clear, actionable verdict a user can take to their tattoo artist.
- Never fabricate citations or historical sources. Leave historical_usage_notes null if not definitively verified.
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


def _build_user_prompt(req: VerificationRequest) -> str:
    lang_str = req.language.strip() if req.language else "auto"
    parts = [f"Phrase to verify: \"{req.phrase}\""]
    if lang_str.lower() != "auto":
        parts.append(f"Target language specified by user: {lang_str}")
    else:
        parts.append("Target language: Auto-detect")

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

    user_prompt = _build_user_prompt(req)

    try:
        response = await client.aio.models.generate_content(
            model=settings.verification_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
    except Exception as e:
        raise VerificationError(f"Gemini API request failed: {e}") from e

    raw_text = _clean_json_text(response.text or "")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise VerificationError(f"Model did not return valid JSON: {e}\nRaw output: {raw_text}") from e

    detected_lang = parsed.get("detected_language") or (req.language if req.language and req.language != "auto" else "Detected Language")
    final_language = req.language if req.language and req.language != "auto" else detected_lang

    return VerificationResult(
        input_phrase=req.phrase,
        language=final_language,
        detected_language=detected_lang,
        intended_meaning=req.intended_meaning,
        grammatically_valid=parsed.get("grammatically_valid", False),
        confidence=parsed.get("confidence", "low"),
        corrected_phrase=parsed.get("corrected_phrase"),
        literal_translation=parsed.get("literal_translation", ""),
        issues=parsed.get("issues", []),
        historical_usage_notes=parsed.get("historical_usage_notes"),
        recommendation=parsed.get("recommendation", ""),
    )


